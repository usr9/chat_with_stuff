# Chat with PostgreSQL using Claude

A natural language interface for PostgreSQL databases using Anthropic's Claude 3.5 Sonnet. This tool allows users to query PostgreSQL databases using plain English, with Claude handling the translation to SQL and result interpretation.

## Features

- Natural language to SQL translation using Claude 3.5 Sonnet
- Dynamic schema detection and mapping
- Support for complex SQL queries including joins and aggregations
- RESTful API endpoint for database queries (to be implemented)
- Docker support for containerized deployment

## Prerequisites

- Python 3.9+
- PostgreSQL database
- Docker (optional)
- Anthropic API key

## Installation

1. Clone the repository:

```bash
git clone https://github.com/usr9/chat_with_stuff
cd chat_with_postgres
```

2. Set up environment variables:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```txt
ANTHROPIC_API_KEY=your_key_here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
PORT=5000  # Optional, defaults to 5000
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

Run the interactive CLI:

```bash
python main.py
```

Example queries:

- "Show me all tables in the database"
- "What are the top 10 customers by order value?"
- "Find all orders from last month with their customer details"

#### API Endpoints

To be impelemented

## Database Support

The application automatically detects and maps your database schema, including:

- Tables and their columns
- Data types
- Foreign key relationships
- Indexes and constraints

This information is used to help Claude generate accurate SQL queries based on your schema.

## Docker Support

To be implemented.

## Acknowledgments

- [Anthropic](https://www.anthropic.com/) for Claude API
- Flask framework contributors
- SQLAlchemy contributors
