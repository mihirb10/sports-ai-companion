# SportsAI

## Overview

SportsAI is a Flask-based web application providing an intelligent conversational interface for NFL football discussions. It leverages Anthropic's Claude AI for expert analysis on NFL tactics, live game information, fantasy football advice, and strategic discussions. The application features user authentication, persistent conversation history, a modern dark-themed chat interface, and PWA capabilities. Key capabilities include route and play analysis with interactive visual diagrams, proactive fantasy injury monitoring, integration of NFL news and injury reports, detailed game analysis using play-by-play data, ESPN Fantasy Football API integration for real-time roster management, and YouTube video highlights for specific plays. The AI agent is designed as a stats-focused sports expert, prioritizing quantifiable facts and data.

## User Preferences

Preferred communication style: Simple, everyday language. Keep responses concise - just key stats and salient points, avoid lengthy explanations.

## System Architecture

### Authentication

SportsAI integrates Replit Auth for OAuth2-based authentication (Google, email/password). User sessions are managed with Flask-Login, and accounts are stored in PostgreSQL with isolated conversation history.

### Database

Utilizes PostgreSQL (Replit's managed service) with SQLAlchemy ORM. The schema includes `Users`, `OAuth`, `Conversations`, and `Predictions` tables. `Users` stores profile data (display_name, custom_avatar_path), fantasy team data (fantasy_scoring_system, fantasy_roster, espn_league_id, espn_s2, espn_swid). `Conversations` stores serialized JSON history, fantasy context, and recent analysis context per user, enabling AI memory for follow-up questions. `Predictions` stores user predictions with text, outcome (pending/correct/incorrect), and created/resolved dates.

### Frontend

Built with Vanilla JavaScript, HTML5, and CSS3, following a single-page application pattern with `login.html` and `index.html`. Features a modern dark theme (`#1a1a1a`). A mobile-friendly bottom navigation bar includes Chat, Scores, Fantasy, Predictions, and Profile tabs.
- **Chat Tab**: Full-height container with message bubbles and an auto-expanding input box.
- **Scores Tab**: Displays live NFL scores with real-time auto-refresh every 30 seconds when games are live, a week selector, and expandable game cards showing detailed scoring plays, play-by-play updates, and team statistics.
- **Fantasy Tab**: Complete fantasy team management with scoring system selection (PPR, Half PPR, Standard), manual player roster entry with position-based slots (QB, RB, WR, TE, FLEX, K, DEF, Bench, IR), dynamic add/delete slot functionality, and optional ESPN Fantasy Football API integration via League ID and cookies. Data stored in User table (fantasy_scoring_system, fantasy_roster, espn_league_id, espn_s2, espn_swid).
- **Predictions Tab**: Tracks all user predictions with accuracy stats (% correct, total made, outstanding), list view with status badges (pending/correct/incorrect), manual prediction entry form, and AI-assisted saving via chat (agent detects predictions and offers to save them).
- **Profile Tab**: User profile management with custom display name input, avatar upload (PNG, JPEG, WebP up to 5MB), and 5 comic book style preset football player avatars.
Tab state persists in localStorage, and all views use CSS-based toggling. Custom user avatars are displayed in chat messages.

### Progressive Web App (PWA)

Implemented as a PWA for native app-like behavior:
- Custom App Icon (192×192, 512×512, 180×180 for iOS).
- Full PWA manifest (`static/manifest.json`).
- Service Worker (`static/sw.js`) for intelligent caching and offline support.
- Custom "Install App" button appears in the header when available.
- Supports Android (Chrome), iOS (Safari), and desktop browsers, opening full-screen in standalone mode.

### Backend

A Flask application using an application-factory pattern. Key components:
- SQLAlchemy ORM for database interactions.
- Replit Auth blueprint for login.
- Main Flask app handling routes and business logic.
- `NFLCompanion` class manages AI interaction and tool use.
Conversations are database-backed, and `@require_login` protects chat routes.

### API Integration

Exposes a RESTful JSON API with endpoints like `/chat`, `/auth/login`, `/auth/logout`, `/api/profile`, `/api/fantasy`, `/api/predictions`, `/api/scores`, and `/api/game/<game_id>`. Authentication uses Replit Auth's OAuth flow. Error handling includes try-catch for external APIs and graceful degradation.
- **Profile Management**: `/api/profile` handles custom avatar uploads (to `/static/uploads/avatars/`) and preset avatar selection, with validation for type and size (max 5MB).
- **Fantasy Team Management**: `/api/fantasy` saves/loads fantasy team data including scoring system, roster, and ESPN credentials.
- **Predictions Management**: `/api/predictions` handles GET (retrieve all user predictions), POST (create new prediction), and PATCH (update prediction outcome). Calculates accuracy stats as correct / (total - outstanding).
- **Scores API**: `/api/scores` calculates current NFL gameweek, fetches live scores from ESPN's public API, and caches results hourly.
- **Game Details API**: `/api/game/<game_id>` fetches detailed game information including scoring plays, play-by-play data, and team statistics from ESPN.

### Security

Measures include OAuth2 + OpenID Connect via Replit Auth with PKCE, secure session management, API keys in Replit Secrets, and ORM-based SQL injection prevention. User input is sanitized, and Claude's safety features manage content moderation.

## External Dependencies

### AI Service

**Anthropic Claude API**: Utilizes Claude Sonnet 4 for conversational AI and tool/function calling. Requires `ANTHROPIC_API_KEY`.

### Authentication Service

**Replit Auth**: OpenID Connect provider for Google and email/password authentication, managing user profiles and token refreshes.

### Database Service

**PostgreSQL**: Replit's managed (Neon-backed) service for persistent storage of user data, OAuth tokens, and conversation histories.

### Live Sports Data

**ESPN API**: Public endpoint providing live NFL scores, game statuses, team statistics, and play-by-play data via tool calling.

### YouTube Video Integration

**YouTube Data API v3**: Integrated using a direct API key (`YOUTUBE_API_KEY`) for embedding NFL highlights. Employs a dual-search strategy for embeddable fan content and official NFL fallback links, ensuring only one video per request, no exposed URLs, and dark-themed responsive embeds. Gracefully handles quota limits.

### ESPN Fantasy Football Integration

**ESPN Fantasy Football API**: Integrated via `espn-api` Python library to fetch real-time fantasy team data (roster, matchups, standings). Users configure their fantasy team via the Fantasy tab, which stores credentials and roster in the User table. AI agent never asks for credentials in chat - always directs users to Fantasy tab. Agent loads fantasy data from User table for personalized advice.

### Python Dependencies

Key libraries: `flask`, `flask-sqlalchemy`, `flask-login`, `anthropic`, `psycopg2-binary`, `sqlalchemy`, `requests`, `espn-api`, `feedparser`, `matplotlib`, `gunicorn`.

### Hosting Platform

**Replit**: Optimized for deployment on Replit, leveraging its managed PostgreSQL, secrets management, and Gunicorn.

### Static Assets

Custom CSS with variables for theming, Vanilla JavaScript for interactivity, and SVG icons.