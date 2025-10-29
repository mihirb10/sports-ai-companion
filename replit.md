# SportsAI

## Overview

SportsAI is a Flask-based web application providing an intelligent conversational interface for NFL football discussions. It leverages Anthropic's Claude AI for expert analysis on NFL tactics, live game information, fantasy football advice, and strategic discussions. The application features user authentication, persistent conversation history, and a modern, dark-themed chat interface. Key capabilities include route and play analysis with interactive visual diagrams (displayed as thumbnail galleries with fullscreen lightbox viewing), proactive fantasy injury monitoring, integration of NFL news and injury reports, detailed game analysis using play-by-play data, **ESPN Fantasy Football API integration** for real-time roster management and personalized fantasy advice, and **YouTube video highlights** for watching specific plays and touchdowns directly in the chat interface. Route/play analysis covers the entire current season (9 games) by default. The AI agent is designed as a stats-focused sports expert, prioritizing quantifiable facts and data in its responses.

**Visual Diagrams** are shown automatically inline when users:
- Ask what a specific route, play, or defensive coverage is (e.g., "What's a post route?", "What is Cover 2?")
- Request play/route/coverage recommendations (e.g., "What route beats zone?", "What coverage should I use?")
- Ask about a player's favorite routes or plays (e.g., "What are Travis Kelce's best routes?")
- Ask about a play that just happened in a live game

Diagrams appear inline with each description (not grouped at the bottom). Three types: routes (QB+WR only), plays (full formation with QB/RB/OL/WR), and coverages (defensive formations with zones in red).

**Video Highlights** are embedded directly in chat responses when users:
- Ask to watch specific plays (e.g., "Show me that touchdown")
- Request game highlights (e.g., "Chiefs vs Bills highlights")
- Want to see player-specific plays (e.g., "Mahomes best throws this season")

Videos are fetched via YouTube Data API through Replit's YouTube connector and displayed as responsive embedded players matching the dark theme.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Authentication Architecture

SportsAI integrates Replit Auth for OAuth2-based authentication, supporting Google and email/password login. User sessions are managed with Flask-Login, allowing persistent access across devices. User accounts are stored in PostgreSQL, each with isolated conversation history.

### Database Architecture

The application uses PostgreSQL (via Replit's managed service) with SQLAlchemy ORM. The schema includes tables for `Users` (storing Replit Auth IDs and profile info), `OAuth` (for tokens and browser session keys), and `Conversations` (storing serialized JSON conversation history, fantasy context, and recent analysis context per user). The `recent_analysis_context` field enables the AI to remember route/play analysis when users respond affirmatively to follow-up questions. Conversation records are lazily created and linked to `user_id` for persistence.

### Frontend Architecture

Built with Vanilla JavaScript, HTML5, and CSS3, the frontend follows a single-page application pattern. It features a `login.html` for unauthenticated access and an `index.html` for the chat interface. The UI boasts a modern dark theme (`#1a1a1a` primary background) inspired by Claude/Gemini, with a full-height chat container, message bubbles (user 👤, assistant 🏈), an auto-expanding input box, and smooth animations.

### Progressive Web App (PWA) Features

SportsAI is implemented as a Progressive Web App, enabling installation on mobile devices with native app-like behavior:
- **Custom App Icon**: Professional football-themed icon (192×192, 512×512, 180×180 for iOS)
- **Manifest Configuration**: Full PWA manifest (`static/manifest.json`) with app metadata, theme colors, and installation shortcuts
- **Service Worker**: Offline support with intelligent caching strategy (`static/sw.js`) for core assets
- **Install Button**: Custom "Install App" button appears in the header when PWA installation is available
- **Cross-Platform Support**: Works on Android (Chrome), iOS (Safari), and desktop browsers
- **Standalone Mode**: Opens full-screen without browser UI when installed
- **Offline Capability**: Cached assets allow basic functionality without internet connection

Installation methods:
1. **Automatic**: Custom "Install App" button in header (when available)
2. **Manual Android**: Chrome menu → "Install app" or "Add to Home Screen"
3. **Manual iOS**: Safari Share → "Add to Home Screen"

### Backend Architecture

The backend is a Flask application utilizing an application-factory pattern. Core components include:
- **Models**: SQLAlchemy ORM for database interactions.
- **Authentication**: Replit Auth blueprint for login management.
- **Application**: Main Flask app handling routes and business logic.
- **NFLCompanion Class**: Manages AI interaction and tool use.

Key design decisions include database-backed persistence for conversations, the application factory pattern for modularity, and `@require_login` decorators to protect chat routes. The `NFLCompanion` class implements Anthropic's tool use API for dynamic data access.

### API Integration Pattern

The application exposes a RESTful JSON API with endpoints like `/chat` (for AI interaction), `/auth/login`, and `/auth/logout`. Authentication is handled via Replit Auth, redirecting users through the OAuth flow. Error handling involves try-catch blocks for external API calls, graceful degradation, and redirects for authentication failures.

### Security Considerations

Security measures include OAuth2 + OpenID Connect via Replit Auth with PKCE, secure session management, API keys stored in Replit Secrets, and database security via connection pooling and ORM-based SQL injection prevention. User input is sanitized, and Claude's safety features manage content moderation.

## External Dependencies

### AI Service Integration

**Anthropic Claude API**: Utilizes Claude Sonnet 4 for conversational AI, including tool/function calling for dynamic data retrieval. Requires `ANTHROPIC_API_KEY`.

### Authentication Service

**Replit Auth**: Serves as the OpenID Connect provider, configured for Google and email/password authentication. Manages user profiles and token refreshes.

### Database Service

**PostgreSQL**: Provided by Replit (Neon-backed), used for persistent storage of user data, OAuth tokens, and conversation histories. Accessed via Flask-SQLAlchemy and Psycopg2.

### Live Sports Data

**ESPN API**: Provides live NFL scores, game statuses, team statistics, and play-by-play data. This is a public endpoint requiring no API key and is integrated via tool calling.

### YouTube Video Integration

**YouTube Data API v3**: Integrated via Replit's YouTube connector for searching and embedding NFL highlights, touchdowns, and specific plays. The connector manages OAuth2 credentials automatically, providing secure API access through environment variables. The `search_play_highlights` tool constructs smart search queries combining player names, teams, play types, and dates to find relevant videos. Videos are embedded directly in chat responses as responsive iframe players with dark-themed styling matching the app's design.

Key features:
- **Smart Query Building**: Combines player, team, play type, and date to find accurate highlights
- **Automatic Embedding**: First video is embedded inline; additional videos are provided as clickable links
- **Responsive Design**: Videos scale appropriately on mobile/desktop with 16:9 aspect ratio
- **Dark Theme Integration**: iframe styling matches the app's dark color scheme with rounded corners and shadows
- **Graceful Quota Handling**: When YouTube API daily quota is exceeded, the system automatically provides direct YouTube search links as fallback (quota resets at midnight Pacific Time)

### ESPN Fantasy Football Integration

**ESPN Fantasy Football API**: Integrated via the `espn-api` Python library to fetch real-time fantasy team data including roster, matchups, and standings. **Per-user credential storage** ensures each user's ESPN league credentials are stored in their individual database record. The integration provides:
- **Real roster data**: Pulls actual team roster with player names, positions, points, and injury statuses
- **Current matchup**: Shows live scores and projections for the current week's matchup
- **League standings**: Displays win-loss records and league rankings
- **Personalized advice**: AI uses actual roster data to provide start/sit recommendations and fantasy strategy
- **Automatic credential reuse**: Once credentials are provided, they're automatically used for all future requests

**First-Time User Onboarding Flow**:
When users ask about fantasy football for the first time, the AI presents a structured onboarding message explaining:
1. **Option 1**: Manually input roster (for users who prefer manual tracking)
2. **Option 2**: Connect ESPN league (recommended for automatic roster sync)

For ESPN integration, the AI provides:
- Clear instructions on where to find League ID (in the ESPN URL)
- Step-by-step guide to extract ESPN_S2 and SWID cookies from browser developer tools (required for private leagues only)
- A markdown table format for users to fill out their credentials

**Credential Storage & Security**:
- Credentials are stored in each user's `fantasy_context` database field (JSON)
- No global environment variables - each user has their own isolated credentials
- Supports both public leagues (League ID only) and private leagues (League ID + ESPN_S2 + SWID)
- Credentials are automatically injected when calling ESPN API tools

**Two-Step Team Selection with Context Retention**:
1. First call shows all teams in the league
2. AI asks "Tell me which team is yours and I'll pull your current roster, this week's matchup, and give you personalized start/sit recommendations! 🎯"
3. System sets `awaiting_team_selection` flag in user's fantasy_context
4. User's next message is automatically treated as their team name selection
5. System injects context telling AI the user's message is their team selection
6. System remembers team name for automatic use in all future requests
7. Flag is cleared once roster data is successfully fetched

Error handling includes specific messages for invalid credentials, expired cookies, rate limiting, and league access issues.

### Python Dependencies

Key Python libraries include `flask`, `flask-sqlalchemy`, `flask-login`, `anthropic`, `psycopg2-binary`, `sqlalchemy`, `requests`, `espn-api` (for ESPN Fantasy Football integration), `feedparser` (for NFL news), `matplotlib` (for route/play diagrams), and `gunicorn` for production deployment.

### Hosting Platform

**Replit**: The application is optimized for Replit deployment, leveraging its managed PostgreSQL, secrets management, and Gunicorn for scaling.

### Static Assets

The frontend uses custom CSS with variables for theming, Vanilla JavaScript for interactivity, and SVG icons for UI elements.