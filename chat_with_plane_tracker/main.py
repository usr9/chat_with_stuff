from typing import List, Dict, Any
import anthropic
import logging
from plane_tracker import get_aircraft_in_box, Aircraft
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def format_aircraft_for_claude(aircraft: Aircraft) -> Dict[str, Any]:
    """
    Format an Aircraft object into a Claude-friendly dictionary.
    
    Args:
        aircraft: Aircraft object to format
        
    Returns:
        Dictionary with formatted aircraft data
    """
    return {
        "icao24": aircraft.icao24,
        "callsign": aircraft.callsign,
        "country": aircraft.origin_country,
        "position": {
            "latitude": aircraft.latitude,
            "longitude": aircraft.longitude,
            "altitude": aircraft.altitude
        },
        "velocity": aircraft.velocity,
        "heading": aircraft.heading,
        "timestamp": aircraft.timestamp.isoformat()
    }

def create_tool_definition() -> List[Dict[str, Any]]:
    """
    Create the tool definition for Claude API.
    
    Returns:
        List containing the tool definition dictionary
    """
    return [{
        "name": "get_aircraft",
        "description": "Get real-time information about aircraft within a specified geographic bounding box. Returns a list of aircraft with their positions, callsigns, and other flight data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "min_lat": {
                    "type": "number",
                    "description": "Minimum latitude of bounding box"
                },
                "max_lat": {
                    "type": "number",
                    "description": "Maximum latitude of bounding box"
                },
                "min_lon": {
                    "type": "number",
                    "description": "Minimum longitude of bounding box"
                },
                "max_lon": {
                    "type": "number",
                    "description": "Maximum longitude of bounding box"
                }
            },
            "required": ["min_lat", "max_lat", "min_lon", "max_lon"]
        }
    }]

def process_claude_conversation(client: anthropic.Anthropic, user_query: str) -> str:
    """
    Process a conversation with Claude, handling tool usage and responses.
    
    Args:
        client: Anthropic client instance
        user_query: Initial user query string
        
    Returns:
        str: Claude's final response text
    """
    # Initialize message history
    message_history = [{"role": "user", "content": user_query}]
    
    # Get initial response from Claude
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=create_tool_definition(),
        messages=message_history
    )
    
    # Add Claude's response to message history
    message_history.append({
        "role": "assistant",
        "content": response.content
    })

    # Handle tool usage if needed
    if response.stop_reason == "tool_use":
        for content in response.content:
            if content.type == "tool_use":
                logger.info(f"Tool input parameters: {content.input}")
                
                # Get aircraft data
                aircraft_list = get_aircraft_in_box(
                    min_lat=content.input["min_lat"],
                    max_lat=content.input["max_lat"],
                    min_lon=content.input["min_lon"],
                    max_lon=content.input["max_lon"]
                )
                
                # Format aircraft data
                formatted_aircraft = [
                    format_aircraft_for_claude(aircraft) 
                    for aircraft in aircraft_list
                ]
                
                # Add tool result to message history
                message_history.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": str(formatted_aircraft)
                    }]
                })
                
                # Get final response from Claude
                final_response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    tools=create_tool_definition(),
                    messages=message_history
                )
                
                # Return Claude's final response text
                for final_content in final_response.content:
                    if final_content.type == "text":
                        return final_content.text
                        
    # If no tool was used, return the initial response text
    for content in response.content:
        if content.type == "text":
            return content.text

def main() -> None:
    """
    Main function to interact with Claude API using aircraft data.
    Requires ANTHROPIC_API_KEY environment variable to be set.
    """
    try:
        client = anthropic.Anthropic()
        
        while True:
            user_query = input("Enter a query for Claude (or exit to quit): ")
            if user_query.lower() == 'exit':
                break
            
            response = process_claude_conversation(client, user_query)
            print(response)

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()