from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import anthropic
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DBConfig:
    """Database configuration parameters."""
    host: str
    port: int
    database: str
    user: str
    password: str

class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass

class PostgresManager:
    """Manages PostgreSQL database connections and schema information."""
    
    def __init__(self, config: DBConfig):
        """
        Initialize database manager with configuration.
        
        Args:
            config: Database configuration object
        """
        self.config = config
        self._connection = None
        self.schema_info = self._fetch_schema_info()

    def _get_connection(self) -> psycopg2.extensions.connection:
        """
        Get or create database connection.
        
        Returns:
            Active database connection
            
        Raises:
            DatabaseError: If connection fails
        """
        try:
            if self._connection is None or self._connection.closed:
                self._connection = psycopg2.connect(
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.user,
                    password=self.config.password
                )
            return self._connection
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            raise DatabaseError(f"Failed to connect to database: {e}") from e

    def _fetch_schema_info(self) -> Dict[str, Any]:
        """
        Fetch database schema information including tables, columns, and relationships.
        
        Returns:
            Dictionary containing schema information
            
        Raises:
            DatabaseError: If schema fetch fails
        """
        try:
            conn = self._get_connection()
            schema_info = {
                "tables": {},
                "relationships": []
            }
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get tables and columns
                cur.execute("""
                    SELECT 
                        t.table_name,
                        array_agg(DISTINCT c.column_name) as columns,
                        array_agg(DISTINCT c.data_type) as data_types
                    FROM information_schema.tables t
                    JOIN information_schema.columns c 
                        ON c.table_name = t.table_name
                    WHERE t.table_schema = 'public'
                    GROUP BY t.table_name;
                """)
                
                for row in cur.fetchall():
                    schema_info["tables"][row["table_name"]] = {
                        "columns": row["columns"],
                        "data_types": row["data_types"]
                    }
                
                # Get foreign key relationships
                cur.execute("""
                    SELECT
                        tc.table_name as table_from,
                        kcu.column_name as column_from,
                        ccu.table_name AS table_to,
                        ccu.column_name AS column_to
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY';
                """)
                
                schema_info["relationships"] = [dict(row) for row in cur.fetchall()]
                
            return schema_info
            
        except psycopg2.Error as e:
            logger.error(f"Error fetching schema information: {e}")
            raise DatabaseError(f"Failed to fetch schema information: {e}") from e

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results.
        
        Args:
            query: SQL query string to execute
            
        Returns:
            List of dictionaries containing query results
            
        Raises:
            DatabaseError: If query execution fails
        """
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                results = cur.fetchall()
                conn.commit()
                return [dict(row) for row in results]
                
        except psycopg2.Error as e:
            logger.error(f"Query execution error: {e}")
            raise DatabaseError(f"Failed to execute query: {e}") from e

def create_tool_definition(schema_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create the tool definition for Claude API.
    
    Args:
        schema_info: Database schema information
        
    Returns:
        List containing the tool definition dictionary
    """
    return [{
        "name": "execute_sql",
        "description": f"""Execute SQL queries on the PostgreSQL database with the following schema:
        
Tables and Columns:
{', '.join(f'{table}: {cols["columns"]}' for table, cols in schema_info["tables"].items())}

Relationships:
{', '.join(f'{r["table_from"]}.{r["column_from"]} -> {r["table_to"]}.{r["column_to"]}' for r in schema_info["relationships"])}

Return results as a list of records. Only generate SELECT queries unless explicitly asked for other operations.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to execute"
                }
            },
            "required": ["query"]
        }
    }]

def process_claude_conversation(
    client: anthropic.Anthropic,
    db_manager: PostgresManager,
    user_query: str
) -> None:
    """
    Process a conversation with Claude, handling database queries and responses.
    
    Args:
        client: Anthropic client instance
        db_manager: Database manager instance
        user_query: Initial user query string
    """
    message_history = [{"role": "user", "content": user_query}]
    
    try:
        # Get initial response from Claude
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            tools=create_tool_definition(db_manager.schema_info),
            messages=message_history
        )
        
        message_history.append({
            "role": "assistant",
            "content": response.content
        })

        # Handle tool usage if needed
        if response.stop_reason == "tool_use":
            for content in response.content:
                if content.type == "tool_use":
                    logger.info(f"Executing SQL query: {content.input['query']}")
                    
                    # Execute query and get results
                    try:
                        results = db_manager.execute_query(content.input["query"])
                        
                        # Add results to message history
                        message_history.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": content.id,
                                "content": str(results)
                            }]
                        })
                        
                        # Get final response from Claude
                        final_response = client.messages.create(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=1024,
                            tools=create_tool_definition(db_manager.schema_info),
                            messages=message_history
                        )
                        
                        # Print Claude's final response
                        for final_content in final_response.content:
                            if final_content.type == "text":
                                print(final_content.text)
                                
                    except DatabaseError as e:
                        message_history.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": content.id,
                                "content": str(e),
                                "is_error": True
                            }]
                        })

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

def main() -> None:
    """
    Main function to interact with Claude API using database queries.
    Requires environment variables for database connection and ANTHROPIC_API_KEY.
    """
    try:
        # Initialize database connection
        db_config = DBConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        
        db_manager = PostgresManager(db_config)
        client = anthropic.Anthropic()
        
        print("Connected to database. Schema loaded.")
        print("Available tables:", ", ".join(db_manager.schema_info["tables"].keys()))
        
        while True:
            user_query = input("Enter your question (or 'exit' to quit): ")
            if user_query.lower() == "exit":
                break
            
            process_claude_conversation(client, db_manager, user_query)

    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()