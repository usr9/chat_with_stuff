# Plane Tracker with Claude Integration

A real-time aircraft tracking system that integrates the OpenSky Network API with Anthropic's Claude 3.5 Sonnet for natural language processing of aircraft location queries.

## Features

- Real-time aircraft tracking within specified geographic boundaries
- Natural language processing of location queries using Claude 3.5 Sonnet
- RESTful API endpoint for querying aircraft data
- Docker support for containerized deployment

## Prerequisites

- Python 3.9+
- Docker (optional)
- Anthropic API key

## Installation

1. Clone the repository:

```bash
git clone https://github.com/usr9/chat_with_stuff.git
cd chat_with_plane_tracker
```

2. Set up environment variables:

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```txt
ANTHROPIC_API_KEY=your_key_here
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

- "What aircraft are currently flying over the Baltics?"
- "Show me planes near London Heathrow"
- "List aircraft in the New York area"

### API Server

Start the Flask server:

```bash
python api.py
```

The server will start on `http://localhost:5000` (or your configured PORT).

#### API Endpoints

- `GET /health` - Health check endpoint
- `POST /api/query` - Process natural language aircraft queries

Example API request:

```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What aircraft are flying over Berlin?"}'
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- [OpenSky Network](https://opensky-network.org/) for aircraft data
- [Anthropic](https://www.anthropic.com/) for Claude API
- Flask framework contributors
