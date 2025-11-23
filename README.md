# Real-Time Podcast AI Assistant

A real-time AI assistant for podcast transcription, topic tracking, and fact-checking.

## Project Structure

```
lauzhack-2025/
├── backend/             # Backend FastAPI application
│   ├── app/
│   │   ├── api/        # API endpoints and WebSocket handlers
│   │   ├── core/       # Core configuration and state management
│   │   ├── engines/    # Topic and fact-checking engines
│   │   └── utils/      # Utility functions
│   ├── tests/          # Test files and test data
│   ├── run.py          # Backend entry point
│   └── requirements.txt # Python dependencies
├── frontend/           # Frontend application (to be implemented)
├── docs/              # Documentation and guides
└── README.md          # This file
```

## Features

- **Real-time Transcription**: Using Deepgram's WebSocket API for live audio transcription
- **Topic Tracking**: Semantic drift detection and topic tree generation
- **Fact Checking**: 3-step pipeline (Detect → Search → Verify) for verifying claims
- **WebSocket API**: Real-time bidirectional communication

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

4. Run the backend server:
   ```bash
   python run.py
   # Or: python -m backend
   ```

The server will start on `http://localhost:8765`

### Frontend Setup

The frontend is not yet implemented. See `frontend/README.md` for planned structure.

## Testing

Run the WAV file streaming test:
```bash
cd backend/tests
python test_wav_stream.py
```

## Documentation

See the `docs/` directory for detailed guides:
- Architecture and design decisions
- API documentation
- Deployment guides
- Feature-specific guides

## License

See [LICENSE](LICENSE) file for details.

## Development

This project was created for LauzHack 2025.
