# SQAI(SQL Query AI) CLI Tool Usage Guide

## Overview

The SQAI CLI(`sql-query-ai-cli.py`) tool provides a command-line interface for querying SQL databases using either direct SQL queries or natural language queries powered by LlamaIndex and Gemini.

## Quick Start

### Prerequisites
1. Set up your environment variables:
```bash
export DATABASE_URL="postgresql://username:password@host:port/database"
export GEMINI_API_KEY="your-gemini-api-key"  # Required for NL queries only
```

2. Activate your virtual environment:
```bash
source venv/bin/activate
```

## Usage Modes

### 1. Interactive Mode (Recommended)
Start an interactive session where you can execute multiple queries:

```bash
python sql-query-ai-cli.py --interactive
```

**Interactive Commands:**
- `sql <query>` - Execute direct SQL query
- `nl <query>` - Execute natural language query ('nl' can be omitted)
- `table <name>` - Change current table
- `show tables` - List available tables
- `help` - Show help
- `quit` or `exit` - Exit the program

**Example Interactive Session:**
```
Query> table users
Table changed to: users

Query> sql SELECT COUNT(*) FROM users
=== Executing SQL: SELECT COUNT(*) FROM users ===
Found 1 records:
count
-----
150

Query> nl How many active users do we have?
=== Natural Language Query: How many active users do we have? ===
Response: Based on the data, there are 120 active users in the system.

Query> quit
```

### 2. Single Query Mode

Execute a single query and exit:

#### Direct SQL Query (Method 1)
```bash
# Basic SQL query
python sql-query-ai-cli.py -t "users" -q "SELECT * FROM users LIMIT 5" -s

# With schema-qualified table
python sql-query-ai-cli.py -t "public.users" -q "SELECT name, email FROM public.users WHERE active = true" -s
```

#### Natural Language Query
```bash
# Simple NL query
python sql-query-ai-cli.py -t "products" -q "Show me all products with price greater than 100"

# Complex NL query
python sql-query-ai-cli.py -t "orders" -q "What is the average order value for last month?"
```

## Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--table` | `-t` | Table name to query (supports schema.table format) |
| `--query` | `-q` | Query to execute |
| `--sql` | `-s` | Use direct SQL instead of natural language |
| `--interactive` | | Run in interactive mode |
| `--database-url` | | Override DATABASE_URL environment variable |
| `--help` | `-h` | Show help message |

## Examples

### Basic Usage
```bash
# Show all records from a table (direct SQL)
python sql-query-ai-cli.py -t "metadata_store" -q "SELECT * FROM metadata_store" -s

# Natural language query
python sql-query-ai-cli.py -t "sales" -q "Show me the top 10 customers by revenue this year"
```

## Error Handling

The CLI tool provides helpful error messages for common issues:

- **Database Connection**: Clear messages when connection fails
- **Missing Table**: Warnings when specified table is not found
- **API Key Missing**: Instructions for setting GEMINI_API_KEY
- **Invalid SQL**: SQL syntax error details
- **Network Issues**: Timeout and connectivity error handling

## Features

### Implemented
- Interactive and single-query modes
- Direct SQL and natural language queries
- Schema-qualified table support
- Real-time table switching
- Comprehensive error handling
- Built-in help system

### Planned Enhancements
- Support OpenAI or other LLMs
- Query result export (CSV/JSON)
- Batch query execution
- To add

## Troubleshooting

### Common Issues

1. **"Table not found" warnings**
   - The tool will still attempt to query the table
   - Check table name spelling and schema qualification

2. **Natural language queries not working**
   - Ensure GEMINI_API_KEY is set
   - Check internet connectivity
   - Falls back to SQL interpretation if NL engine fails

3. **Database connection errors**
   - Verify DATABASE_URL format
   - Check database server accessibility
   - Confirm credentials are correct

### Getting Help

Use the built-in help:
```bash
python sql-query-ai-cli.py --help
```

Or in interactive mode:
```bash
Query> help
```

## Security Notes

- Never hardcode credentials in scripts
- Use environment variables for sensitive information
- The tool uses parameterized queries to prevent SQL injection
- Consider using database users with minimal required privileges