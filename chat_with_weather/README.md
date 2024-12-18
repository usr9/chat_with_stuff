# Weather Service with Claude Integration

A Python application that combines OpenWeatherMap's weather data with Anthropic's Claude 3.5 Sonnet for natural language weather queries. Get detailed weather information for any city using conversational language.

## Features

- Natural language interface for weather queries using Claude 3.5 Sonnet
- Real-time weather data from OpenWeatherMap API including:
  - Current temperature and "feels like" temperature in Celsius
  - Humidity percentage and pressure (hPa)
  - Wind speed (m/s) and direction (degrees)
  - Weather condition descriptions

## Prerequisites

- Python 3.9+
- OpenWeatherMap API key
- Anthropic API key

## Installation

1. Clone the repository:

```bash
git clone https://github.com/usr9/chat_with_stuff
cd weather-service-claude
```

1. Set up environment variables:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```txt
ANTHROPIC_API_KEY=your_claude_key_here
OPENWEATHER_API_KEY=your_openweather_key_here
```

1. Install dependencies:

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

- "What's the weather like in London?"
- "Is it raining in Tokyo right now?"
- "How hot is it in Dubai today?"
- "What's the wind speed in Chicago?"

## Acknowledgments

- [OpenWeatherMap](https://openweathermap.org/) for weather data API
- [Anthropic](https://www.anthropic.com/) for Claude API
- [python-dotenv](https://github.com/theskumar/python-dotenv) contributors
