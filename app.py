#!/usr/bin/env python3
"""
NFL AI Companion - Web Version for Replit
Flask-based web interface with chat UI
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import anthropic
import requests
import json
import os
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))
CORS(app, supports_credentials=True)

class NFLCompanion:
    def __init__(self, anthropic_api_key: str):
        """Initialize the NFL AI Companion."""
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        
        self.system_prompt = """You are an enthusiastic and knowledgeable NFL companion - think of yourself as a passionate football fan who loves deep tactical discussions.

Your capabilities:
- Discuss NFL tactics, play-calling, defensive schemes, offensive strategies
- Analyze player performance and matchups
- Provide fantasy football advice (start/sit, trade analysis, waiver pickups)
- Access live scores, standings, and stats when needed via tools
- Remember our conversation history to build on previous discussions
- Share insights on coaching decisions and game management

Your personality:
- Passionate about football but never overbearing
- Can discuss X's and O's in depth - coverages, route concepts, blocking schemes
- Offer both casual fan perspectives and analytical insights
- Honest about uncertainty (don't make up stats)
- Supportive with fantasy decisions but realistic about variance

When discussing tactics:
- Reference specific plays, formations (I-formation, spread, bunch, etc.)
- Discuss defensive concepts (Cover 2, Cover 3, man blitz, zone blitz, etc.)
- Analyze offensive line play, pass protection schemes
- Break down route combinations and passing concepts
- Consider situational football (down & distance, game script, clock management)

Engage naturally - ask follow-up questions, share interesting observations, and build a genuine football discussion partnership."""

    def get_live_scores(self) -> dict:
        """Fetch live NFL scores."""
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            games = []
            for event in data.get('events', []):
                game_info = {
                    'name': event.get('name', 'N/A'),
                    'status': event.get('status', {}).get('type', {}).get('description', 'N/A'),
                    'home_team': event.get('competitions', [{}])[0].get('competitors', [{}])[0].get('team', {}).get('displayName', 'N/A'),
                    'away_team': event.get('competitions', [{}])[0].get('competitors', [{}])[1].get('team', {}).get('displayName', 'N/A'),
                    'home_score': event.get('competitions', [{}])[0].get('competitors', [{}])[0].get('score', 'N/A'),
                    'away_score': event.get('competitions', [{}])[0].get('competitors', [{}])[1].get('score', 'N/A'),
                    'date': event.get('date', 'N/A')
                }
                games.append(game_info)
            
            return {
                'success': True,
                'games': games,
                'week': data.get('week', {}).get('number', 'N/A'),
                'season_type': data.get('season', {}).get('type', 'N/A')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Could not fetch live scores at this time'
            }

    def get_team_stats(self, team_name: str) -> dict:
        """Get team statistics."""
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for team in data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
                if team_name.lower() in team.get('team', {}).get('displayName', '').lower():
                    team_data = team.get('team', {})
                    return {
                        'success': True,
                        'name': team_data.get('displayName', 'N/A'),
                        'record': team_data.get('record', {}).get('items', [{}])[0].get('summary', 'N/A'),
                        'logo': team_data.get('logos', [{}])[0].get('href', 'N/A')
                    }
            
            return {
                'success': False,
                'message': f'Could not find team: {team_name}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def chat(self, user_message: str, conversation_history: list) -> tuple:
        """Main chat interface with tool use."""
        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Define tools
        tools = [
            {
                "name": "get_live_scores",
                "description": "Fetches current NFL scores, game status, and week information. Use this when the user asks about current games, scores, or what's happening right now in the NFL.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_team_stats",
                "description": "Gets statistics and information for a specific NFL team including their record. Use this when discussing a specific team's performance.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "team_name": {
                            "type": "string",
                            "description": "The name of the NFL team (e.g., 'Chiefs', 'Patriots', 'Cowboys')"
                        }
                    },
                    "required": ["team_name"]
                }
            }
        ]
        
        # Make API call
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=self.system_prompt,
            messages=conversation_history,
            tools=tools
        )
        
        # Handle tool use
        while response.stop_reason == "tool_use":
            tool_use_block = next(block for block in response.content if block.type == "tool_use")
            tool_name = tool_use_block.name
            tool_input = tool_use_block.input
            
            # Execute tool
            if tool_name == "get_live_scores":
                tool_result = self.get_live_scores()
            elif tool_name == "get_team_stats":
                tool_result = self.get_team_stats(tool_input["team_name"])
            else:
                tool_result = {"error": "Unknown tool"}
            
            # Add to history - convert content blocks to serializable format
            serialized_content = []
            for block in response.content:
                if block.type == "text":
                    serialized_content.append({
                        "type": "text",
                        "text": block.text
                    })
                elif block.type == "tool_use":
                    serialized_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })

            conversation_history.append({
                "role": "assistant",
                "content": serialized_content
            })
            
            conversation_history.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_block.id,
                        "content": json.dumps(tool_result)
                    }
                ]
            })
            
            # Continue conversation
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=self.system_prompt,
                messages=conversation_history,
                tools=tools
            )
        
        # Extract text response
        assistant_message = ""
        for block in response.content:
            if hasattr(block, "text"):
                assistant_message += block.text
        
        # Add to history
        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        return assistant_message, conversation_history


# Initialize companion
api_key = os.environ.get('ANTHROPIC_API_KEY')
if not api_key:
    print("⚠️  WARNING: ANTHROPIC_API_KEY not set in environment variables!")
    print("Set it in Replit Secrets or your environment")

companion = NFLCompanion(api_key) if api_key else None


@app.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages."""
    if not companion:
        return jsonify({
            'error': 'API key not configured. Please set ANTHROPIC_API_KEY in Replit Secrets.'
        }), 500
    
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get or initialize conversation history
        if 'conversation_history' not in session:
            session['conversation_history'] = []
        
        conversation_history = session['conversation_history']
        
        # Get response
        response, updated_history = companion.chat(user_message, conversation_history)
        
        # Update session
        session['conversation_history'] = updated_history
        
        return jsonify({
            'response': response,
            'success': True
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@app.route('/reset', methods=['POST'])
def reset():
    """Reset conversation history."""
    session['conversation_history'] = []
    return jsonify({'success': True, 'message': 'Conversation reset'})


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'api_key_configured': bool(api_key)
    })


if __name__ == '__main__':
    # Run on all interfaces for Replit
    app.run(host='0.0.0.0', port=5000, debug=True)
