from dataclasses import dataclass
from typing import List, Optional
import httpx
from requests.exceptions import RequestException
import logging
from datetime import datetime
from rich import print

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Aircraft:
    icao24: str
    callsign: Optional[str]
    origin_country: str
    longitude: float
    latitude: float
    altitude: float
    velocity: float
    heading: float
    timestamp: datetime

class OpenSkyAPIError(Exception):
    """Custom exception for OpenSky API errors."""
    pass

def get_aircraft_in_box(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
) -> List[Aircraft]:
    """
    Fetch aircraft within a specified bounding box from OpenSky Network API.

    Args:
        min_lat: Minimum latitude of bounding box
        max_lat: Maximum latitude of bounding box
        min_lon: Minimum longitude of bounding box
        max_lon: Maximum longitude of bounding box
        username: Optional OpenSky Network username
        password: Optional OpenSky Network password

    Returns:
        List of Aircraft objects within the specified bounding box

    Raises:
        OpenSkyAPIError: If the API request fails
        ValueError: If coordinates are invalid
    """
    # Input validation
    if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
        raise ValueError("Latitude must be between -90 and 90 degrees")
    if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
        raise ValueError("Longitude must be between -180 and 180 degrees")
    if min_lat > max_lat or min_lon > max_lon:
        raise ValueError("Minimum coordinates must be less than maximum coordinates")

    url = "https://opensky-network.org/api/states/all"
    params = {
        "lamin": min_lat,
        "lamax": max_lat,
        "lomin": min_lon,
        "lomax": max_lon
    }

    try:
        response = httpx.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("states"):
            logger.info("No aircraft found in the specified region")
            return []

        aircraft_list = []
        for state in data["states"]:
            # OpenSky API returns null for some fields, handle them properly
            if not all(state[i] is not None for i in [5, 6, 7, 9, 10]):
                continue

            aircraft = Aircraft(
                icao24=state[0],
                callsign=state[1].strip() if state[1] else None,
                origin_country=state[2],
                longitude=float(state[5]),
                latitude=float(state[6]),
                altitude=float(state[7]),
                velocity=float(state[9]),
                heading=float(state[10]),
                timestamp=datetime.fromtimestamp(state[3])
            )
            aircraft_list.append(aircraft)

        logger.info(f"Found {len(aircraft_list)} aircraft in the specified region")
        return aircraft_list

    except RequestException as e:
        logger.error(f"Failed to fetch data from OpenSky Network: {str(e)}")
        raise OpenSkyAPIError(f"API request failed: {str(e)}") from e
    except (ValueError, KeyError, IndexError) as e:
        logger.error(f"Error parsing API response: {str(e)}")
        raise OpenSkyAPIError(f"Failed to parse API response: {str(e)}") from e

# Example usage
if __name__ == "__main__":
    print(get_aircraft_in_box(42.4, 42.8, 23.1, 23.5))
