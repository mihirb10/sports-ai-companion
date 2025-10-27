# SportsAI

## Overview

SportsAI is a Flask-based web application that provides an intelligent conversational interface for NFL football discussions. The application leverages Anthropic's Claude AI to deliver expert analysis on NFL tactics, live game information, fantasy football advice, and strategic football discussions. It features a modern, dark-themed chat interface inspired by Claude and Gemini, optimized for deployment on Replit and accessible from any device.

## Recent Changes

**October 27, 2025**: Complete UI redesign
- Rebranded from "NFL AI Companion" to "SportsAI"
- Implemented dark theme interface (#1a1a1a background) matching Claude/Gemini aesthetic
- Redesigned header with football logo (🏈) and SportsAI branding in top left
- Moved input box to bottom with modern rounded design
- Created centered welcome screen with example prompt cards
- Added smooth animations and modern hover effects
- Improved mobile responsiveness

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack**: Vanilla JavaScript, HTML5, CSS3

The frontend implements a single-page application (SPA) pattern with a modern dark-themed chat interface inspired by Claude and Gemini. The architecture is deliberately simple to ensure fast loading times and compatibility with Replit's hosting environment.

**Key Design Decisions**:
- **No Framework Dependencies**: Uses vanilla JavaScript to minimize bundle size and deployment complexity on Replit
- **Server-Side Rendering**: Initial HTML is rendered by Flask templates, with dynamic chat interactions handled via JavaScript
- **Dark Theme Design**: Modern dark color scheme with CSS variables for consistent theming
- **Mobile-First Responsive Design**: CSS implements a flexible layout system that adapts to various screen sizes
- **Stateless Frontend**: All conversation state is maintained server-side in Flask sessions, preventing client-side storage complications

**UI Components**:
- Top navigation bar with logo, app name, and reset button
- Full-height chat container with centered welcome screen
- Message bubbles with avatars (user and assistant)
- Bottom-fixed input section with auto-expanding textarea
- Example prompt cards for quick interactions
- Typing indicator for feedback during API calls
- Smooth fade-in animations for messages

**Color Scheme**:
- Primary background: #1a1a1a (dark)
- Secondary background: #2d2d2d
- Text primary: #ececec (light)
- Text secondary: #b0b0b0
- Accent color: #5865f2 (blue)
- User messages: #5865f2 background
- Assistant messages: Dark background with light text

### Backend Architecture

**Framework**: Flask (Python web framework)

The backend follows a simple request-response pattern optimized for Replit's serverless-like environment.

**Architecture Pattern**: MVC-inspired structure
- **Models**: `NFLCompanion` class encapsulates AI interaction logic
- **Views**: Flask route handlers in `app.py`
- **Templates**: Jinja2 templates in `templates/` directory

**Key Design Decisions**:

1. **Session-Based State Management**
   - Problem: Need to maintain conversation history across multiple HTTP requests
   - Solution: Flask sessions store conversation history server-side
   - Rationale: Simpler than implementing a database for this use case; works well with Replit's ephemeral environment
   - Trade-offs: Sessions are memory-based and cleared on restart, but this is acceptable for a conversational AI where users can easily start new chats

2. **Synchronous Request Handling**
   - Problem: AI API calls can take several seconds
   - Solution: Synchronous Flask routes with frontend loading indicators
   - Alternatives Considered: WebSockets or Server-Sent Events for streaming responses
   - Trade-offs: Simpler implementation and deployment; acceptable latency for chat use case

3. **Tool/Function Calling Pattern**
   - The `NFLCompanion` class implements Anthropic's tool use API for accessing live NFL data
   - Tools are defined for fetching live scores and game information
   - This enables the AI to access real-time data when discussing current games

4. **No Database Layer**
   - Problem: Persistence requirements for conversation history
   - Solution: Session-based ephemeral storage
   - Rationale: Conversations are transient by nature; permanent storage adds complexity without significant user benefit
   - Future Consideration: Could add optional database for conversation export/history features

### API Integration Pattern

**RESTful JSON API**:
- `POST /chat`: Accepts user messages, returns AI responses
- `POST /reset`: Clears conversation history
- `GET /health`: Health check endpoint for API key configuration
- All responses follow consistent JSON structure: `{success: bool, response?: string, error?: string}`

**Error Handling Strategy**:
- Try-catch blocks around external API calls
- Graceful degradation with user-friendly error messages
- Frontend displays error states in the chat interface

### Security Considerations

1. **API Key Management**: Uses environment variables (`ANTHROPIC_API_KEY`) accessed via `os.environ`
2. **Session Security**: Flask secret key generated using `secrets.token_hex()` if not provided via environment
3. **Input Validation**: User input is transmitted as-is to the AI service; Claude's built-in safety features handle content moderation

## External Dependencies

### AI Service Integration

**Anthropic Claude API**:
- Primary service for conversational AI capabilities
- Uses `anthropic` Python SDK (>=0.39.0)
- Implements tool/function calling for live data access
- Configuration: Requires `ANTHROPIC_API_KEY` environment variable

**System Prompt Design**: A comprehensive system prompt defines the AI's personality, capabilities, and knowledge domain (NFL tactics, fantasy football, game analysis)

### Live Sports Data

**NFL Data Source**: 
- The application includes methods for fetching live NFL scores and game data
- Implementation details suggest external API integration (specific endpoint not visible in provided code)
- Uses Python `requests` library for HTTP calls

### Web Framework Stack

**Flask** (>=3.0.0):
- Lightweight WSGI web application framework
- Chosen for simplicity and Replit compatibility
- Handles routing, templating, and session management

**Python-dotenv** (>=1.0.0):
- Environment variable management for local development
- Allows `.env` file configuration alongside Replit's Secrets

### Hosting Platform

**Replit Optimization**:
- `.replit` configuration file for automated deployment
- Flask development server suitable for Replit's environment
- No production WSGI server (gunicorn/uWSGI) required for Replit deployment
- Static file serving handled by Flask's built-in capabilities

**Environment Configuration**:
- `ANTHROPIC_API_KEY`: Required for AI functionality
- `FLASK_SECRET_KEY`: Optional; auto-generated if not provided
- Replit Secrets system recommended for sensitive values

### Static Assets

**CSS Framework**: Custom CSS with CSS variables for dark theme
**JavaScript**: No external libraries; pure vanilla JS for DOM manipulation and fetch API calls
**Icons**: SVG icons for send button and reset button
