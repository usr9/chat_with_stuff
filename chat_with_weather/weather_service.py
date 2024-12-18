# weather_service.py

from dataclasses import dataclass
from typing import Dict, Any, Optional
import httpx
from requests.exceptions import RequestException
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WeatherData:
    """Container for weather information."""
    temperature: float  # in Celsius
    feels_like: float
    humidity: int      # percentage
    pressure: int      # hPa
    wind_speed: float  # meters/sec
    wind_direction: int  # degrees
    description: str
    timestamp: datetime
    location: str
    country: str

class WeatherAPIError(Exception):
    """Custom exception for OpenWeatherMap API errors."""
    pass

class WeatherService:
    """Service for fetching weather data from OpenWeatherMap API."""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the weather service.
        
        Args:
            api_key: OpenWeatherMap API key. If not provided, will try to get from environment.
            
        Raises:
            ValueError: If no API key is available
        """
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenWeatherMap API key is required. Set OPENWEATHER_API_KEY environment variable.")
    
    def get_weather(self, city: str) -> WeatherData:
        """
        Fetch current weather data for a specific city.
        
        Args:
            city: Name of the city to get weather for
            
        Returns:
            WeatherData object containing current weather information
            
        Raises:
            WeatherAPIError: If the API request fails or returns invalid data
            ValueError: If city parameter is invalid
        """
        if not city.strip():
            raise ValueError("City name cannot be empty")
        
        params: Dict[str, str] = {
            "q": city,
            "appid": self.api_key,
            "units": "metric"  # Use Celsius
        }
        
        try:
            response = httpx.get(
                self.BASE_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return WeatherData(
                temperature=data["main"]["temp"],
                feels_like=data["main"]["feels_like"],
                humidity=data["main"]["humidity"],
                pressure=data["main"]["pressure"],
                wind_speed=data["wind"]["speed"],
                wind_direction=data["wind"]["deg"],
                description=data["weather"][0]["description"],
                timestamp=datetime.fromtimestamp(data["dt"]),
                location=data["name"],
                country=data["sys"]["country"]
            )
            
        except RequestException as e:
            logger.error(f"Failed to fetch weather data: {str(e)}")
            raise WeatherAPIError(f"API request failed: {str(e)}") from e
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing weather data: {str(e)}")
            raise WeatherAPIError(f"Failed to parse API response: {str(e)}") from e
        

# Example usage
if __name__ == "__main__":
    service = WeatherService()
    try:
        data = service.get_weather("San Francisco")
        print(f"Current weather in {data.location}, {data.country}:")
        print(f"Temperature: {data.temperature}°C")
        print(f"Feels like: {data.feels_like}°C")
        print(f"Humidity: {data.humidity}%")
        print(f"Pressure: {data.pressure} hPa")
        print(f"Wind: {data.wind_speed} m/s, {data.wind_direction}°")
        print(f"Description: {data.description}")
        print(f"Timestamp: {data.timestamp}")
    except WeatherAPIError as e:
        print(f"Failed to fetch weather data: {e}")