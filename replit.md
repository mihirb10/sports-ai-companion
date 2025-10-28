# SportsAI

## Overview

SportsAI is a Flask-based web application that provides an intelligent conversational interface for NFL football discussions with user authentication and persistent conversation history. The application leverages Anthropic's Claude AI to deliver expert analysis on NFL tactics, live game information, fantasy football advice, and strategic football discussions. It features a modern, dark-themed chat interface inspired by Claude and Gemini, with Google and email/password authentication via Replit Auth.

## Recent Changes

**October 28, 2025**: Play-by-play data integration + game analysis capabilities
- **Added ESPN play-by-play API**: Agent can now access detailed game data including scoring plays, drive summaries, box scores, and player stats
- **New game analysis features**: Users can ask "What happened in the Chiefs game?" and get comprehensive stat-driven recaps
- **Enhanced data depth**: Scoring play details, drive efficiency metrics (yards/plays/time), top performer stats from specific games
- Agent intelligently chains tools: fetches game IDs from live scores, then retrieves detailed play-by-play data

**October 28, 2025**: Major AI personality redesign + logout button
- **Transformed agent into stats-focused sports nerd**: Leads with statistics and numbers, uses extensive bullet points, includes emojis to highlight data (📊 📈 🔥)
- **Reduced chattiness**: Agent asks fewer questions, lets user drive conversation, only prompts when topic naturally concludes
- **Data-first approach**: Every response prioritizes quantifiable facts over feelings/opinions
- Added logout button in top right corner of chat interface
- Full conversation context retained across all interactions (already implemented, verified)

**October 28, 2025**: Added user authentication and database persistence
- Integrated Replit Auth for Google and email/password login
- Set up PostgreSQL database for user accounts and conversation storage
- Conversations now persist across sessions and devices for logged-in users
- Added login landing page before chat access
- Protected all chat routes with authentication middleware
- Refactored to application-factory pattern with SQLAlchemy ORM

**October 27, 2025**: Complete UI redesign
- Rebranded from "NFL AI Companion" to "SportsAI"
- Implemented dark theme interface (#1a1a1a background) matching Claude/Gemini aesthetic
- Redesigned header with football logo (🏈) and SportsAI branding
- Moved input box to bottom with modern rounded design
- Created centered welcome screen
- Removed reset button - conversations persist automatically
- Added smooth animations and modern hover effects
- Improved mobile responsiveness

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Authentication Architecture

**Replit Auth Integration**:
- OAuth2-based authentication using Replit's OpenID Connect provider
- Supports Google login and email/password authentication
- User session management with Flask-Login
- Browser session keys for multi-device support
- Automatic token refresh for seamless user experience

**User Management**:
- Users stored in PostgreSQL with unique IDs from Replit Auth
- Profile information includes email, name, and profile image
- Each user has isolated conversation history
- OAuth tokens securely stored and managed

### Database Architecture

**Technology Stack**: PostgreSQL (via Replit's managed database)

**Schema Design**:
1. **Users Table**
   - id (String, Primary Key) - from Replit Auth sub claim
   - email, first_name, last_name, profile_image_url
   - created_at, updated_at timestamps
   
2. **OAuth Table**
   - Stores OAuth tokens and browser session keys
   - Links authentication tokens to users
   - Supports multi-device login
   
3. **Conversations Table**
   - id (Integer, Primary Key)
   - user_id (Foreign Key to Users)
   - history (JSON Text) - serialized conversation messages
   - created_at, updated_at timestamps

**Key Design Decisions**:
- JSON serialization for conversation history allows flexible message formats
- One conversation per user model - simple and efficient
- Automatic lazy creation of conversation records on first chat
- Database-backed sessions replace ephemeral Flask sessions

### Frontend Architecture

**Technology Stack**: Vanilla JavaScript, HTML5, CSS3

The frontend implements a single-page application pattern with authentication-aware routing.

**Key Pages**:
1. **Login Page** (`login.html`)
   - Displays when user is not authenticated
   - Clean, centered design matching main chat aesthetic
   - "Sign In" button redirects to Replit Auth flow

2. **Chat Interface** (`index.html`)
   - Only accessible to authenticated users
   - Modern dark-themed chat interface
   - No reset button - conversations persist automatically

**UI Components**:
- Top navigation bar with SportsAI logo and branding
- Full-height chat container with centered welcome screen
- Message bubbles with avatars (user 👤 and assistant 🏈)
- Bottom-fixed input section with auto-expanding textarea
- Typing indicator for API call feedback
- Smooth fade-in animations for messages

**Color Scheme**:
- Primary background: #1a1a1a (dark)
- Secondary background: #2d2d2d
- Text primary: #ececec (light)
- Text secondary: #b0b0b0
- Accent color: #5865f2 (blue)

### Backend Architecture

**Framework**: Flask with application-factory pattern

**Architecture Components**:
- **Models** (`models.py`): SQLAlchemy ORM models for User, OAuth, Conversation
- **Authentication** (`replit_auth.py`): Replit Auth blueprint and login management
- **Application** (`app.py`): Main Flask app with routes and business logic
- **NFLCompanion Class**: AI interaction logic with tool use capabilities

**Key Design Decisions**:

1. **Database-Backed Persistence**
   - Replaces ephemeral session storage
   - Conversations tied to user_id for cross-device access
   - JSON serialization preserves full conversation context including tool use

2. **Application Factory Pattern**
   - `create_app()` function initializes all components
   - Database and login manager initialized via `init_app()`
   - Replit Auth blueprint registered at `/auth` prefix
   - Enables better testing and configuration management

3. **Protected Routes**
   - `@require_login` decorator protects chat endpoints
   - Automatic redirect to login for unauthenticated users
   - Health check endpoint remains public

4. **Tool/Function Calling Pattern**
   - NFLCompanion class implements Anthropic's tool use API
   - Tools for live NFL scores and team statistics
   - Full conversation context preserved including tool interactions

### API Integration Pattern

**RESTful JSON API**:
- `POST /chat`: Accepts user messages, returns AI responses (requires auth)
- `POST /reset`: Clears conversation history (requires auth)
- `GET /health`: Health check endpoint (public)
- `GET /auth/login`: Initiates Replit Auth login flow
- `GET /auth/logout`: Logs out user and ends Replit session

**Authentication Flow**:
1. User clicks "Sign In" on landing page
2. Redirected to `/auth/login`
3. Replit Auth handles authentication (Google or email/password)
4. User redirected back to app with auth token
5. Token exchanged for user info and session created
6. User can access chat interface

**Error Handling Strategy**:
- Try-catch blocks around external API calls
- Graceful degradation with user-friendly error messages
- Authentication errors redirect to error page
- Frontend displays error states in chat interface

### Security Considerations

1. **Authentication & Authorization**
   - OAuth2 + OpenID Connect via Replit Auth
   - PKCE (Proof Key for Code Exchange) for security
   - Session-based user tracking with secure cookies
   - All chat routes protected by authentication middleware

2. **API Key Management**
   - `ANTHROPIC_API_KEY` stored in Replit Secrets
   - `SESSION_SECRET` required for secure session management
   - Never exposed to frontend or logs

3. **Database Security**
   - Connection string via `DATABASE_URL` environment variable
   - Connection pooling with health checks
   - User data isolated by user_id foreign keys

4. **Input Validation**
   - User input sanitized before storage
   - Claude's built-in safety features handle content moderation
   - SQL injection prevented by SQLAlchemy ORM

## External Dependencies

### AI Service Integration

**Anthropic Claude API**:
- Claude Sonnet 4 model for conversational AI
- Tool/function calling for live data access
- Requires `ANTHROPIC_API_KEY` environment variable
- Handles NFL tactics, fantasy advice, and game analysis

### Authentication Service

**Replit Auth**:
- OpenID Connect provider for authentication
- Supports Google, GitHub, Apple, email/password
- Configured to use Google and email/password only
- Automatic user profile management
- Token refresh for session persistence

### Database Service

**PostgreSQL** (Neon-backed via Replit):
- Managed database with automatic backups
- Environment variables: DATABASE_URL, PGHOST, PGPORT, etc.
- Flask-SQLAlchemy ORM for database operations
- Psycopg2 driver for PostgreSQL connectivity

### Live Sports Data

**ESPN API**:
- Live NFL scores and game status
- Team statistics and records
- No API key required (public endpoint)
- Integrated via tool calling

### Python Dependencies

**Core Framework**:
- flask (>=3.0.0) - Web framework
- flask-sqlalchemy (>=3.1.0) - Database ORM
- flask-login (>=0.6.0) - User session management
- flask-dance (>=7.1.0) - OAuth integration
- gunicorn (>=23.0.0) - Production WSGI server

**Database**:
- psycopg2-binary - PostgreSQL driver
- sqlalchemy (>=2.0.0) - Database toolkit

**Authentication**:
- pyjwt - JWT token handling
- oauthlib - OAuth protocol implementation

**Other**:
- anthropic (>=0.39.0) - Claude AI SDK
- requests (>=2.31.0) - HTTP requests
- python-dotenv (>=1.0.0) - Environment variables

### Hosting Platform

**Replit Optimization**:
- Application factory pattern for production deployment
- Gunicorn configured for autoscale deployment
- ProxyFix middleware for proper HTTPS handling
- Database connection pooling for reliability

**Environment Configuration**:
- `ANTHROPIC_API_KEY`: Required for AI functionality
- `SESSION_SECRET`: Required for secure sessions
- `DATABASE_URL`: Auto-configured by Replit
- `REPL_ID`: Auto-set for OAuth client ID
- `ISSUER_URL`: Replit's OpenID Connect endpoint

### Static Assets

**CSS Framework**: Custom CSS with CSS variables for dark theme
**JavaScript**: Vanilla JS for DOM manipulation and fetch API
**Icons**: SVG icons for UI elements
