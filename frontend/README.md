# Podcast AI Assistant - Frontend

Modern React + TypeScript frontend for the Real-Time Podcast AI Assistant.

## Features

- **Audio File Upload**: Drag-and-drop or click to upload WAV/MP3 files
- **Real-time Processing Status**: Visual feedback during transcription and analysis
- **Topic Visualization**:
  - **Agenda View**: List-based navigation with search functionality
  - **Timeline View**: Chronological flow visualization
- **Transcript Display**: Full transcript with copy functionality and reading stats
- **Fact-Checking Results**: Color-coded verdicts with sources and explanations
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Axios** for API communication
- **Lucide React** for icons
- **Context API** for state management

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend server running on `http://localhost:8000`

### Installation

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. (Optional) Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env if needed
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:3000`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── AudioUpload.tsx        # File upload component
│   │   ├── ProcessingStatus.tsx   # Processing progress indicator
│   │   ├── TopicAgenda.tsx        # Agenda view of topics
│   │   ├── TopicTimeline.tsx      # Timeline view of topics
│   │   ├── TranscriptView.tsx     # Transcript display
│   │   └── FactCheckCard.tsx      # Fact-check result card
│   ├── context/
│   │   └── AppContext.tsx         # Global state management
│   ├── services/
│   │   └── api.ts                 # API client and methods
│   ├── types/
│   │   └── index.ts               # TypeScript type definitions
│   ├── App.tsx                    # Main app component
│   ├── main.tsx                   # Entry point
│   └── index.css                  # Global styles
├── public/
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

## Key Components

### AudioUpload
- Handles file selection via drag-and-drop or file picker
- Validates file types (WAV, MP3)
- Displays selected file information
- Initiates processing

### TopicAgenda
- List-based topic navigation
- Search functionality for topics and keywords
- Expandable details for each topic
- Visual indicators for selected topics

### TopicTimeline
- Vertical timeline visualization
- Interactive hover effects
- Topic progression tracking
- Chronological flow representation

### TranscriptView
- Full transcript display
- One-click copy functionality
- Reading statistics (word count, reading time)
- Paragraph-based formatting

### FactCheckCard
- Color-coded verdicts (Verified/False/Uncertain)
- Confidence percentage
- Expandable sources with external links
- Key facts summary

## Architecture

### State Management
- **Context API** for global state
- Centralized processing logic
- Type-safe state updates

### API Integration
- Axios client with TypeScript types
- Upload progress tracking
- Error handling
- Proxy configuration for CORS

### Extensibility
The frontend is designed to support future features:
- **WebSocket Support**: `AudioStreamClient` class ready for live streaming
- **Real-time Updates**: Infrastructure for incremental topic/fact updates
- **Progress Tracking**: Stage-based processing visualization

## Future Enhancements

### Planned Features (TODOs in code)
- [ ] WebSocket support for real-time streaming (`src/services/api.ts`)
- [ ] Live progress indicator for streaming (`TopicTimeline.tsx`)
- [ ] Timestamp support for topics
- [ ] Bookmark functionality for important moments
- [ ] Export functionality (PDF, JSON)
- [ ] Audio playback with synchronized transcript
- [ ] Multi-file batch processing

### Migration to Streaming API
When implementing the WebSocket-based streaming:

1. Update `AppContext.tsx` to use `AudioStreamClient`
2. Add incremental state updates for topics and facts
3. Enable real-time UI updates in components
4. Add streaming progress indicators

Example:
```typescript
// In AppContext.tsx
const streamAudio = async (file: File) => {
  const client = new AudioStreamClient();
  await client.connect();

  client.on('transcript', (data) => {
    // Update transcript incrementally
  });

  client.on('topic_update', (data) => {
    // Add new topic to timeline
  });

  // Stream audio chunks...
};
```

## API Integration

The frontend communicates with the backend via:

### Current Endpoint
- `POST /process-audio`: Upload and process complete audio file

### Future Endpoints (for streaming)
- `WS /listen`: WebSocket for real-time audio streaming
- `WS /facts/stream`: WebSocket for fact-check results stream

## Development

### Code Quality
- TypeScript for type safety
- ESLint for code linting
- Consistent component structure
- Comprehensive comments and documentation

### Best Practices
- Component-based architecture
- Separation of concerns
- Reusable components
- Responsive design
- Accessibility considerations

## Troubleshooting

### CORS Issues
If you encounter CORS errors:
1. Ensure the backend is running on `http://localhost:8000`
2. Check that Vite proxy is configured correctly in `vite.config.ts`
3. Verify backend CORS settings

### Build Errors
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Type Errors
Ensure TypeScript dependencies are up to date:
```bash
npm install -D typescript @types/react @types/react-dom
```

## Contributing

When adding new features:
1. Update TypeScript types in `src/types/index.ts`
2. Add proper error handling
3. Update this README
4. Add TODO comments for future enhancements
5. Maintain consistent code style

## License

See main project LICENSE file.
