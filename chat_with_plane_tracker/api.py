from typing import Dict, Any, Tuple
from flask import Flask, request
from logging.config import dictConfig
from dotenv import load_dotenv
import os
import anthropic

from main import process_claude_conversation

# Configure logging
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'api.log',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi', 'file']
    }
})

load_dotenv()

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

@app.errorhandler(400)
def bad_request(error: Any) -> Tuple[Dict[str, Any], int]:
    """Handle bad request errors."""
    return {
        'error': 'Bad Request',
        'message': str(error)
    }, 400

@app.errorhandler(500)
def internal_error(error: Any) -> Tuple[Dict[str, Any], int]:
    """Handle internal server errors."""
    app.logger.error(f'Server Error: {str(error)}')
    return {
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }, 500

@app.route('/health', methods=['GET'])
def health_check() -> Tuple[Dict[str, str], int]:
    """
    Health check endpoint.
    
    Returns:
        Tuple containing response dictionary and HTTP status code
    """
    return {'status': 'healthy'}, 200

@app.route('/api/query', methods=['POST'])
def query_claude() -> Tuple[Dict[str, Any], int]:
    """
    Process a natural language query using Claude.
    
    Expected JSON body:
        {
            "query": "string"
        }
    
    Returns:
        Tuple containing response dictionary and HTTP status code
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return {
                'error': 'Missing Data',
                'message': 'Request must include a "query" field'
            }, 400

        # Use existing function from main.py
        response = process_claude_conversation(client, data['query'])
        
        return {'response': response}, 200

    except Exception as e:
        app.logger.error(f'Unexpected error: {str(e)}')
        return {
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }, 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)