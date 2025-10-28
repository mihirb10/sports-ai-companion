# SportsAI

## Overview

SportsAI is a Flask-based web application providing an intelligent conversational interface for NFL football discussions. It leverages Anthropic's Claude AI for expert analysis on NFL tactics, live game information, fantasy football advice, and strategic discussions. The application features user authentication, persistent conversation history, and a modern, dark-themed chat interface. Key capabilities include route and play analysis with visual diagrams, proactive fantasy injury monitoring, integration of NFL news and injury reports, and detailed game analysis using play-by-play data. The AI agent is designed as a stats-focused sports expert, prioritizing quantifiable facts and data in its responses.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Authentication Architecture

SportsAI integrates Replit Auth for OAuth2-based authentication, supporting Google and email/password login. User sessions are managed with Flask-Login, allowing persistent access across devices. User accounts are stored in PostgreSQL, each with isolated conversation history.

### Database Architecture

The application uses PostgreSQL (via Replit's managed service) with SQLAlchemy ORM. The schema includes tables for `Users` (storing Replit Auth IDs and profile info), `OAuth` (for tokens and browser session keys), and `Conversations` (storing serialized JSON conversation history, fantasy context, and recent analysis context per user). The `recent_analysis_context` field enables the AI to remember route/play analysis when users respond affirmatively to follow-up questions. Conversation records are lazily created and linked to `user_id` for persistence.

### Frontend Architecture

Built with Vanilla JavaScript, HTML5, and CSS3, the frontend follows a single-page application pattern. It features a `login.html` for unauthenticated access and an `index.html` for the chat interface. The UI boasts a modern dark theme (`#1a1a1a` primary background) inspired by Claude/Gemini, with a full-height chat container, message bubbles (user 👤, assistant 🏈), an auto-expanding input box, and smooth animations.

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

### Python Dependencies

Key Python libraries include `flask`, `flask-sqlalchemy`, `flask-login`, `anthropic`, `psycopg2-binary`, `sqlalchemy`, `requests`, and `gunicorn` for production deployment.

### Hosting Platform

**Replit**: The application is optimized for Replit deployment, leveraging its managed PostgreSQL, secrets management, and Gunicorn for scaling.

### Static Assets

The frontend uses custom CSS with variables for theming, Vanilla JavaScript for interactivity, and SVG icons for UI elements.