# call_weather.py

from dataclasses import dataclass
from typing import List, Dict, Any
import os
from datetime import datetime
import anthropic
import logging
from weather_service import WeatherService, WeatherData, WeatherAPIError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def format_weather_for_claude(weather: WeatherData) -> Dict[str, Any]:
    """
    Format WeatherData object into a Claude-friendly dictionary.
    
    Args:
        weather: WeatherData object to format
        
    Returns:
        Dictionary with formatted weather data
    """
    return {
        "location": {
            "city": weather.location,
            "country": weather.country
        },
        "temperature": {
            "current": weather.temperature,
            "feels_like": weather.feels_like
        },
        "conditions": {
            "description": weather.description,
            "humidity": weather.humidity,
            "pressure": weather.pressure
        },
        "wind": {
            "speed": weather.wind_speed,
            "direction": weather.wind_direction
        },
        "timestamp": weather.timestamp.isoformat()
    }

def create_tool_definition() -> List[Dict[str, Any]]:
    """
    Create the tool definition for Claude API.
    
    Returns:
        List containing the tool definition dictionary
    """
    return [{
        "name": "get_weather",
        "description": "Get current weather information for a specific city. Returns temperature, " 
                      "humidity, wind speed, and other weather conditions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Name of the city to get weather for"
                }
            },
            "required": ["city"]
        }
    }]

def process_claude_conversation(
    client: anthropic.Anthropic,
    weather_service: WeatherService,
    user_query: str
) -> None:
    """
    Process a conversation with Claude, handling weather data requests and responses.
    
    Args:
        client: Anthropic client instance
        weather_service: WeatherService instance
        user_query: Initial user query string
    """
    message_history = [{"role": "user", "content": user_query}]
    
    try:
        # Get initial response from Claude
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            tools=create_tool_definition(),
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
                    logger.info(f"Getting weather for city: {content.input['city']}")
                    
                    try:
                        # Get weather data
                        weather_data = weather_service.get_weather(content.input["city"])
                        formatted_weather = format_weather_for_claude(weather_data)
                        
                        # Add weather data to message history
                        message_history.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": content.id,
                                "content": str(formatted_weather)
                            }]
                        })
                        
                        # Get final response from Claude
                        final_response = client.messages.create(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=1024,
                            tools=create_tool_definition(),
                            messages=message_history
                        )
                        
                        # Print Claude's final response
                        for final_content in final_response.content:
                            if final_content.type == "text":
                                print(final_content.text)
                                
                    except WeatherAPIError as e:
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
    Main function to interact with Claude API using weather data.
    Requires ANTHROPIC_API_KEY and OPENWEATHER_API_KEY environment variables.
    """
    try:
        weather_service = WeatherService()
        client = anthropic.Anthropic()
        
        while True:
            user_query = input("Enter your weather question (or 'exit' to quit): ")
            if user_query.lower() == "exit":
                break
            
            process_claude_conversation(client, weather_service, user_query)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()