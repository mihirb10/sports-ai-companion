#!/usr/bin/env python3
"""
SportsAI - Flask web application with user authentication
Integrated with Replit Auth for Google and email/password login
"""

from flask import Flask, render_template, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import current_user
import anthropic
import requests
import json
import os
from datetime import datetime
import logging

from models import db, User, Conversation
from replit_auth import login_manager, make_replit_blueprint, require_login

logging.basicConfig(level=logging.DEBUG)

class NFLCompanion:
    def __init__(self, anthropic_api_key: str):
        """Initialize the NFL AI Companion."""
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        
        self.system_prompt = """You are SportsAI - the ultimate NFL statistics and analytics companion. You're a sports data nerd who LOVES numbers, facts, and stats above all else.

🎯 CORE IDENTITY:
You are NOT a chatty friend. You are a walking statistical database and tactical encyclopedia. Think data analyst meets film room obsessive.

📊 RESPONSE STRUCTURE - ALWAYS FOLLOW THIS:
• Lead with STATISTICS and NUMBERS in every response
• Use bullet points extensively for clarity
• Include emojis to highlight key stats (📈 📉 🏆 🔥 💯 ⚡ 🎯)
• Focus on quantifiable facts over feelings or opinions
• Present data in digestible chunks

🚫 WHAT TO AVOID:
• Don't ask unnecessary questions - let the user lead the conversation
• Don't be overly conversational or chatty
• Don't share feelings or subjective opinions without backing them with stats
• ONLY ask questions if:
  - User hasn't engaged in a while and conversation has naturally concluded
  - You need specific clarification about which stats/team/player they want
  - A topic has reached its natural end and they might want another

📈 WHAT TO INCLUDE IN EVERY RESPONSE:
• Specific numbers (yards, percentages, rankings, touchdowns, etc.)
• Historical comparisons with stats
• League averages and where players/teams rank
• Efficiency metrics (yards per attempt, completion %, EPA, DVOA if known)
• Season/career stats, trends over time
• Advanced analytics when relevant (success rate, pressure %, target share, etc.)

🏈 TACTICAL DEPTH:
• Reference specific formations with usage rates
• Cite defensive scheme tendencies with percentages
• Use play-calling stats (pass/run ratios, personnel groupings)
• Quote pressure rates, coverage stats, blocking efficiency
• Down & distance success rates

💬 COMMUNICATION STYLE:
• Be concise but data-rich
• Statistics first, context second
• Bullet points over paragraphs
• Emojis to make stats engaging, not to be friendly
• Let the user drive - respond to what they ask, don't probe for more

🎮 SPECIFIC RESPONSE PATTERNS:

**Fantasy Football Questions:**
• If user asks about fantasy football and hasn't shared their team roster yet, ask them "Who's on your team?" so you can provide personalized advice
• Once you know their team, provide player-specific stats and recommendations

**"Games Today" Questions:**
• Use the get_live_scores tool to fetch current data
• Filter to ONLY show games happening TODAY (check the date field)
• Report scores in bullet points
• Include brief performance summaries (who played well/badly with key stats)
• End with: "What else would you like to know?"

**"Latest Scores" Questions:**
• Use the get_live_scores tool
• Report ALL scores from the most recent game week
• Format as bullet points with final scores
• Include game status (Final, In Progress, Scheduled)

Example good response:
"📊 Patrick Mahomes 2024 Stats:
• 4,183 yards (3rd in NFL)
• 67.5% completion (8th)
• 32 TDs / 11 INTs (2.9:1 ratio)
• 8.4 yards/attempt ⚡
• 26.1 points/game (Chiefs offense ranked 4th)

🎯 Red Zone: 65.2% TD rate (league avg: 58%)
📈 Under pressure: 56.3% completion (elite)"

Remember: You're a stats encyclopedia, not a conversation partner. Numbers over narratives. Facts over feelings."""

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
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
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
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=self.system_prompt,
            messages=conversation_history,
            tools=tools
        )
        
        while response.stop_reason == "tool_use":
            tool_use_block = next(block for block in response.content if block.type == "tool_use")
            tool_name = tool_use_block.name
            tool_input = tool_use_block.input
            
            if tool_name == "get_live_scores":
                tool_result = self.get_live_scores()
            elif tool_name == "get_team_stats":
                tool_result = self.get_team_stats(tool_input["team_name"])
            else:
                tool_result = {"error": "Unknown tool"}
            
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
            
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=self.system_prompt,
                messages=conversation_history,
                tools=tools
            )
        
        assistant_message = ""
        for block in response.content:
            if hasattr(block, "text"):
                assistant_message += block.text
        
        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        return assistant_message, conversation_history


def create_app():
    """Application factory."""
    app = Flask(__name__)
    
    app.secret_key = os.environ.get("SESSION_SECRET")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        'pool_pre_ping': True,
        "pool_recycle": 300,
    }
    
    db.init_app(app)
    login_manager.init_app(app)
    
    with app.app_context():
        db.create_all()
        logging.info("Database tables created")
    
    app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")
    
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        logging.warning("ANTHROPIC_API_KEY not set in environment variables!")
    
    companion = NFLCompanion(api_key) if api_key else None
    
    def get_or_create_conversation(user_id: str) -> Conversation:
        """Get or create conversation for a user."""
        conversation = Conversation.query.filter_by(user_id=user_id).first()
        if not conversation:
            conversation = Conversation(user_id=user_id, history='[]')
            db.session.add(conversation)
            db.session.commit()
        return conversation
    
    @app.route('/')
    def index():
        """Landing/Chat page."""
        if not current_user.is_authenticated:
            return render_template('login.html')
        return render_template('index.html')
    
    @app.route('/chat', methods=['POST'])
    @require_login
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
            
            conversation = get_or_create_conversation(current_user.id)
            conversation_history = json.loads(conversation.history)
            
            response, updated_history = companion.chat(user_message, conversation_history)
            
            conversation.history = json.dumps(updated_history)
            db.session.commit()
            
            return jsonify({
                'response': response,
                'success': True
            })
        
        except Exception as e:
            logging.error(f"Chat error: {e}")
            return jsonify({
                'error': str(e),
                'success': False
            }), 500
    
    @app.route('/reset', methods=['POST'])
    @require_login
    def reset():
        """Reset conversation history."""
        conversation = get_or_create_conversation(current_user.id)
        conversation.history = '[]'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Conversation reset'})
    
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'api_key_configured': bool(api_key)
        })
    
    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
