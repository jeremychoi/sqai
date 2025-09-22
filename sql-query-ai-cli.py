#!/usr/bin/env python3
"""
SQL Query CLI Tool

A command-line interface for querying databases using either direct SQL queries
or natural language queries powered by LlamaIndex and Gemini.

Usage:
    python3 sql-query-cli.py --table TABLE_NAME --query "Your query here"
    python3 sql-query-cli.py -t TABLE_NAME -q "Your query here" -s  # For direct SQL
    python3 sql-query-cli.py --interactive  # Interactive mode

Environment Variables:
    DATABASE_URL: Database connection string (default: postgresql://postgres:postgres@localhost:5432/database)
    GEMINI_API_KEY: Your Gemini API key (required for NL queries)
"""

import os
import sys
import argparse
from typing import Optional
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core import SQLDatabase
from llama_index.llms.gemini import Gemini
from sqlalchemy import create_engine, text


class SQLQueryCLI:
    def __init__(self, database_url: str):
        """Initialize the CLI with database connection."""
        self.database_url = database_url
        self.engine = None
        self.sql_database = None
        self.llm = None
        self.query_engine = None
        self._setup_failure_reason = None
        
    def connect_to_database(self) -> bool:
        """Establish database connection."""
        try:
            self.engine = create_engine(self.database_url)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"✓ Connected to database successfully")
            return True
        except Exception as e:
            print(f"✗ Error connecting to database: {e}")
            return False
    
    def setup_schema_path(self, table_name: str) -> tuple[str, str]:
        """Parse table name and set up schema path if needed."""
        if '.' in table_name:
            schema_name, table_name_only = table_name.split('.', 1)
            try:
                with self.engine.connect() as conn:
                    conn.execute(text(f"SET search_path TO {schema_name}, public"))
                    conn.commit()
                print(f"✓ Set search path to include schema: {schema_name}")
                return schema_name, table_name_only
            except Exception as e:
                print(f"⚠ Warning: Could not set search path for schema {schema_name}: {e}")
                return schema_name, table_name_only
        else:
            return None, table_name
    
    def execute_direct_sql(self, table_name: str, query: str = None) -> bool:
        """Execute direct SQL query (Method 1)."""
        try:
            if query is None:
                # Default query - show all records
                sql_query = f"SELECT * FROM {table_name}"
                print(f"=== All records from {table_name} table (Direct SQL) ===")
            else:
                # Custom SQL query
                sql_query = query
                print(f"=== Executing SQL: {sql_query} ===")
            
            with self.engine.connect() as connection:
                result = connection.execute(text(sql_query))
                rows = result.fetchall()
                columns = result.keys()
                
                if not rows:
                    print("No records found.")
                    return True
                
                # Print column headers
                print(f"Found {len(rows)} records:")
                header = " | ".join(str(col) for col in columns)
                print(header)
                print("-" * len(header))
                
                # Print all records
                for row in rows:
                    print(" | ".join(str(value) if value is not None else "NULL" for value in row))
                
            return True
            
        except Exception as e:
            print(f"✗ Error executing SQL query: {e}")
            return False
    
    def validate_table_exists(self, table_name: str) -> bool:
        """Validate that a table exists by trying a simple query."""
        try:
            # Parse schema and table name
            schema_name, table_name_only = self.setup_schema_path(table_name)
            
            # Try a simple query to check if table exists
            test_query = f"SELECT 1 FROM {table_name} LIMIT 1"
            with self.engine.connect() as connection:
                connection.execute(text(test_query))
                return True
        except Exception:
            return False
    
    def setup_nl_query_engine(self, table_name: str) -> bool:
        """Set up natural language query engine."""
        try:
            # Check for Gemini API key
            if not os.getenv("GEMINI_API_KEY"):
                print("✗ GEMINI_API_KEY environment variable not set.")
                print("You can set it with: export GEMINI_API_KEY='your-api-key-here'")
                return False
            
            # First validate that the table exists
            if not self.validate_table_exists(table_name):
                print(f"⚠ Table {table_name} not found in database")
                self._setup_failure_reason = "table_not_found"
                return False
            
            # Initialize LLM
            self.llm = Gemini(model="models/gemini-2.5-flash", temperature=0.7)
            print("✓ Initialized Gemini LLM")
            
            # Create SQL database wrapper
            self.sql_database = SQLDatabase(self.engine)
            
            # Check available tables and find the correct table name format
            usable_tables = list(self.sql_database.get_usable_table_names())
            print(f"Available tables: {usable_tables}")
            
            # Parse schema and table name
            schema_name, table_name_only = self.setup_schema_path(table_name)
            
            # Determine which table name format to use for the query engine
            # LlamaIndex may discover tables without schema prefix
            target_table = None
            if table_name_only in usable_tables:
                target_table = table_name_only
                print(f"✓ Using table name for query engine: {target_table}")
            elif table_name in usable_tables:
                target_table = table_name
                print(f"✓ Using full table name for query engine: {target_table}")
            else:
                # Fallback to the original table name if not found in usable_tables
                # This can happen with schema-qualified tables
                target_table = table_name_only if table_name_only else table_name
                print(f"✓ Using fallback table name for query engine: {target_table}")
            
            # Create NL Query Engine
            self.query_engine = NLSQLTableQueryEngine(
                sql_database=self.sql_database,
                tables=[target_table],
                llm=self.llm
            )
            
            print("✓ Natural language query engine initialized")
            self._setup_failure_reason = None
            return True
            
        except Exception as e:
            print(f"✗ Error setting up NL query engine: {e}")
            self._setup_failure_reason = "setup_error"
            return False
    
    def execute_nl_query(self, query: str) -> bool:
        """Execute natural language query."""
        try:
            print(f"=== Natural Language Query: {query} ===")
            response = self.query_engine.query(query)
            print(f"Response: {response}")
            return True
        except Exception as e:
            print(f"✗ Error executing NL query: {type(e).__name__}: {e}")
            # Print more detailed error information for debugging
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            return False
    
    def interactive_mode(self):
        """Run in interactive mode."""
        print("=== SQL Query CLI - Interactive Mode ===")
        print("Type 'quit' or 'exit' to stop")
        print("Commands:")
        print("  sql <query>     - Execute direct SQL query")
        print("  nl <query>      - Execute natural language query")
        print("  table <name>    - Set/change table name")
        print("  show tables     - List available tables")
        print("  help           - Show this help")
        print()
        
        # Loop until we get a valid table name
        while True:
            table_name = input("Enter table name: ").strip()
            if not table_name:
                print("Table name is required for interactive mode")
                continue
            
            # First validate that the table exists
            if not self.validate_table_exists(table_name):
                print("Please try again with a valid table name.")
                print()
                continue
            
            # Set up schema path
            self.setup_schema_path(table_name)
            
            # Try to set up NL query engine (optional in interactive mode)
            nl_available = self.setup_nl_query_engine(table_name)
            
            print(f"\nTable set to: {table_name}")
            if nl_available:
                print("Natural language queries are available")
            else:
                print("Only direct SQL queries are available")
            print()
            break
        
        while True:
            try:
                user_input = input("Query> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit']:
                    break
                
                if user_input.lower() == 'help':
                    print("Commands:")
                    print("  sql <query>     - Execute direct SQL query")
                    print("  nl <query>      - Execute natural language query")
                    print("  table <name>    - Set/change table name")
                    print("  show tables     - List available tables")
                    print("  help           - Show this help")
                    continue
                
                if user_input.lower() == 'show tables':
                    if self.sql_database:
                        tables = list(self.sql_database.get_usable_table_names())
                        print(f"Available tables: {tables}")
                    else:
                        try:
                            with self.engine.connect() as conn:
                                result = conn.execute(text("""
                                    SELECT table_name 
                                    FROM information_schema.tables 
                                    WHERE table_schema = 'public'
                                """))
                                tables = [row[0] for row in result.fetchall()]
                                print(f"Available tables: {tables}")
                        except Exception as e:
                            print(f"Error listing tables: {e}")
                    continue
                
                if user_input.startswith('table '):
                    new_table = user_input[6:].strip()
                    if new_table:
                        # Validate the new table exists
                        if not self.validate_table_exists(new_table):
                            print(f"⚠ Table {new_table} not found in database")
                            continue
                        
                        table_name = new_table
                        self.setup_schema_path(table_name)
                        if nl_available:
                            nl_available = self.setup_nl_query_engine(table_name)
                            if nl_available:
                                print(f"✓ Table changed to: {table_name}")
                                print("Natural language queries are available")
                            else:
                                print(f"⚠ Table changed to: {table_name}")
                                print("NL setup failed - only direct SQL queries are available")
                        else:
                            print(f"✓ Table changed to: {table_name}")
                    continue
                
                if user_input.startswith('sql '):
                    sql_query = user_input[4:].strip()
                    if sql_query:
                        self.execute_direct_sql(table_name, sql_query)
                    continue
                
                if user_input.startswith('nl '):
                    if not nl_available:
                        print("Natural language queries are not available. Use 'sql' for direct SQL queries.")
                        continue
                    
                    nl_query = user_input[3:].strip()
                    if nl_query:
                        self.execute_nl_query(nl_query)
                    continue
                
                # Default: treat as natural language query if available, otherwise as SQL
                if nl_available:
                    self.execute_nl_query(user_input)
                else:
                    print("Interpreting as SQL query (prefix with 'sql ' to be explicit):")
                    self.execute_direct_sql(table_name, user_input)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                print("\nGoodbye!")
                break


def main():
    parser = argparse.ArgumentParser(
        description="SQL Query CLI Tool - Query databases with SQL or natural language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -t users -q "SELECT * FROM users LIMIT 5" -s
  %(prog)s --table products --query "Show me all products with price > 100"
  %(prog)s --interactive
  
Environment Variables:
  DATABASE_URL    Database connection string
  GEMINI_API_KEY  Your Gemini API key (required for NL queries)
        """
    )
    
    parser.add_argument(
        "-t", "--table",
        help="Table name to query (can include schema: schema.table)"
    )
    
    parser.add_argument(
        "-q", "--query",
        help="Query to execute (SQL if -s flag is used, otherwise natural language)"
    )
    
    parser.add_argument(
        "-s", "--sql",
        action="store_true",
        help="Use direct SQL query (Method 1) instead of natural language"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/database"),
        help="Database connection URL (default: from DATABASE_URL env var)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.interactive and not args.table:
        print("Error: Table name is required (use -t/--table or --interactive)")
        sys.exit(1)
    
    if not args.interactive and not args.query:
        print("Error: Query is required (use -q/--query or --interactive)")
        sys.exit(1)
    
    # Initialize CLI
    cli = SQLQueryCLI(args.database_url)
    
    # Connect to database
    if not cli.connect_to_database():
        sys.exit(1)
    
    # Run interactive mode
    if args.interactive:
        cli.interactive_mode()
        return
    
    # Run single query mode
    if args.sql:
        # Direct SQL query
        success = cli.execute_direct_sql(args.table, args.query)
    else:
        # Natural language query
        if cli.setup_nl_query_engine(args.table):
            success = cli.execute_nl_query(args.query)
        else:
            # Check why setup failed
            if hasattr(cli, '_setup_failure_reason') and cli._setup_failure_reason == "table_not_found":
                print("✗ Cannot proceed: Table not found in database")
                print("Please verify the table name and ensure it exists in the database")
                sys.exit(1)
            else:
                print("Falling back to direct SQL query...")
                success = cli.execute_direct_sql(args.table, args.query)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
