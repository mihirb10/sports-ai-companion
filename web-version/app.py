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
import feedparser
import re

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

**Game Recap/Analysis Questions:**
• When users ask "What happened in the [team] game?" or "How did [team] do?", use get_play_by_play
• First use get_live_scores to get the game_id, then call get_play_by_play with that ID
• Present scoring plays chronologically with stats
• Highlight top performers with their stat lines
• Include key drive information (yards, plays, result)
• Focus on quantifiable performance metrics

**Injury Questions:**
• When users ask about injuries, injury reports, who's hurt, or player availability, use get_injury_report
• This tool provides guidance on where to find current injury data and explains injury report designations
• Direct users to ESPN's official injury page for the most current information
• Optionally specify team_name for team-specific guidance
• Explain injury designations: Out (will not play), Doubtful (unlikely), Questionable (uncertain), IR (4+ weeks)

**News & Trade Rumors:**
• When users ask about NFL news, trades, rumors, or "what's happening in the league", use get_nfl_news
• Present headlines in bullet point format with brief summaries
• Focus on recent breaking news and significant moves
• Include player stats or team impact where relevant

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
                    'game_id': event.get('id', 'N/A'),
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

    def get_injury_report(self, team_name: str = None) -> dict:
        """Get current NFL injury reports by fetching all teams and their data."""
        try:
            # ESPN doesn't have a public injuries API, so we'll provide guidance
            # and suggest checking ESPN's official injury page or team-specific data
            
            if team_name:
                # For team-specific queries, provide directed guidance
                team_slug = team_name.lower().replace(' ', '-')
                return {
                    'success': True,
                    'message': f'For the most up-to-date {team_name} injury report, check ESPN\'s official injury page.',
                    'guidance': 'Injury reports are typically released on Wednesday, Thursday, and Friday during the season with player status designations (Out, Doubtful, Questionable, IR).',
                    'espn_injuries_url': 'https://www.espn.com/nfl/injuries',
                    'note': 'Real-time injury impacts often show up in game-day inactive lists and play-by-play data.'
                }
            else:
                # General injury report query
                return {
                    'success': True,
                    'message': 'For comprehensive NFL injury reports across all teams, check ESPN\'s official injury page which is updated daily.',
                    'guidance': 'Injury reports are released Wednesday-Friday with player designations: Out (will not play), Doubtful (unlikely to play), Questionable (uncertain), IR (injured reserve, out minimum 4 games).',
                    'espn_injuries_url': 'https://www.espn.com/nfl/injuries',
                    'suggestion': 'Ask about a specific team for targeted injury information, or ask about specific players mentioned in recent news.'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Could not fetch injury report information at this time'
            }

    def get_nfl_news(self, limit: int = 10) -> dict:
        """Get latest NFL news and trade rumors from RSS feeds."""
        try:
            news_items = []
            
            # Try NFL Trade Rumors RSS
            try:
                feed_url = "https://nfltraderumors.co/feed/"
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:limit]:
                    news_items.append({
                        'title': entry.get('title', 'N/A'),
                        'summary': entry.get('summary', 'N/A')[:200] + '...' if len(entry.get('summary', '')) > 200 else entry.get('summary', 'N/A'),
                        'link': entry.get('link', 'N/A'),
                        'published': entry.get('published', 'N/A'),
                        'source': 'NFL Trade Rumors'
                    })
            except Exception as feed_error:
                logging.warning(f"Could not fetch NFL Trade Rumors feed: {feed_error}")
            
            # Fallback or additional source: Pro Football Rumors
            if len(news_items) < limit:
                try:
                    feed_url = "https://www.profootballrumors.com/feed"
                    feed = feedparser.parse(feed_url)
                    
                    for entry in feed.entries[:(limit - len(news_items))]:
                        news_items.append({
                            'title': entry.get('title', 'N/A'),
                            'summary': entry.get('summary', 'N/A')[:200] + '...' if len(entry.get('summary', '')) > 200 else entry.get('summary', 'N/A'),
                            'link': entry.get('link', 'N/A'),
                            'published': entry.get('published', 'N/A'),
                            'source': 'Pro Football Rumors'
                        })
                except Exception as feed_error:
                    logging.warning(f"Could not fetch Pro Football Rumors feed: {feed_error}")
            
            if news_items:
                return {
                    'success': True,
                    'news': news_items,
                    'count': len(news_items)
                }
            else:
                return {
                    'success': False,
                    'message': 'Could not fetch NFL news at this time',
                    'news': []
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Could not fetch NFL news at this time',
                'news': []
            }

    def check_fantasy_team_injuries(self, fantasy_context: dict) -> dict:
        """Check for injury-related news for players on the user's fantasy team."""
        try:
            # Extract player names from fantasy context
            my_team = fantasy_context.get('my_team', [])
            interested_players = fantasy_context.get('interested_players', [])
            all_players = list(set(my_team + interested_players))
            
            if not all_players:
                return {
                    'success': False,
                    'message': 'No fantasy team players to check',
                    'updates': []
                }
            
            # Fetch recent news
            news_result = self.get_nfl_news(limit=20)
            
            if not news_result.get('success', False):
                return {
                    'success': False,
                    'message': 'Could not fetch news for injury check',
                    'updates': []
                }
            
            # Search for injury-related news mentioning the user's players
            injury_updates = []
            injury_keywords = ['injury', 'injured', 'hurt', 'questionable', 'doubtful', 'out', 'ir', 'placed on', 'return', 'activated', 'designated']
            
            for news_item in news_result.get('news', []):
                title = news_item.get('title', '').lower()
                summary = news_item.get('summary', '').lower()
                
                # Check if this news mentions any of the user's players
                for player in all_players:
                    player_lower = player.lower()
                    
                    # Check if player name is in title or summary AND it's injury-related
                    if player_lower in title or player_lower in summary:
                        is_injury_related = any(keyword in title or keyword in summary for keyword in injury_keywords)
                        
                        if is_injury_related:
                            injury_updates.append({
                                'player': player,
                                'headline': news_item.get('title', 'N/A'),
                                'summary': news_item.get('summary', 'N/A'),
                                'link': news_item.get('link', 'N/A'),
                                'source': news_item.get('source', 'N/A')
                            })
            
            return {
                'success': True,
                'updates': injury_updates,
                'count': len(injury_updates)
            }
            
        except Exception as e:
            logging.error(f"Error checking fantasy team injuries: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Could not check fantasy team injuries',
                'updates': []
            }

    def get_play_by_play(self, game_id: str) -> dict:
        """Get detailed play-by-play data for a specific game."""
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={game_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract key game information
            header = data.get('header', {})
            game_info = {
                'game_id': game_id,
                'matchup': header.get('competitions', [{}])[0].get('competitors', [{}])[0].get('team', {}).get('displayName', 'N/A') + ' vs ' + 
                          header.get('competitions', [{}])[0].get('competitors', [{}])[1].get('team', {}).get('displayName', 'N/A'),
                'status': header.get('competitions', [{}])[0].get('status', {}).get('type', {}).get('description', 'N/A')
            }
            
            # Extract scoring plays
            scoring_plays = []
            for play in data.get('scoringPlays', []):
                scoring_plays.append({
                    'quarter': play.get('period', {}).get('number', 'N/A'),
                    'clock': play.get('clock', {}).get('displayValue', 'N/A'),
                    'team': play.get('team', {}).get('displayName', 'N/A'),
                    'description': play.get('text', 'N/A'),
                    'score_value': play.get('scoreValue', 0),
                    'away_score': play.get('awayScore', 0),
                    'home_score': play.get('homeScore', 0)
                })
            
            # Extract drive summaries
            drives = []
            for drive in data.get('drives', {}).get('previous', [])[:10]:  # Last 10 drives
                drives.append({
                    'team': drive.get('team', {}).get('displayName', 'N/A'),
                    'result': drive.get('result', 'N/A'),
                    'plays': drive.get('plays', 0),
                    'yards': drive.get('yards', 0),
                    'time': drive.get('timeElapsed', {}).get('displayValue', 'N/A'),
                    'description': drive.get('description', 'N/A')
                })
            
            # Extract box score stats
            box_score = data.get('boxscore', {})
            team_stats = []
            for team in box_score.get('teams', []):
                stats = {}
                for stat in team.get('statistics', []):
                    stats[stat.get('label', 'N/A')] = stat.get('displayValue', 'N/A')
                
                team_stats.append({
                    'team': team.get('team', {}).get('displayName', 'N/A'),
                    'stats': stats
                })
            
            # Extract player stats
            player_stats = {}
            players = box_score.get('players', [])
            for team_data in players:
                team_name = team_data.get('team', {}).get('displayName', 'N/A')
                player_stats[team_name] = {}
                
                for stat_category in team_data.get('statistics', []):
                    category = stat_category.get('name', 'N/A')
                    player_stats[team_name][category] = []
                    
                    for athlete in stat_category.get('athletes', [])[:5]:  # Top 5 per category
                        player_stats[team_name][category].append({
                            'name': athlete.get('athlete', {}).get('displayName', 'N/A'),
                            'stats': athlete.get('stats', [])
                        })
            
            return {
                'success': True,
                'game_info': game_info,
                'scoring_plays': scoring_plays,
                'drives': drives,
                'team_stats': team_stats,
                'player_stats': player_stats
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Could not fetch play-by-play data for game {game_id}'
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
                "description": "Fetches current NFL scores, game status, and week information. Use this when the user asks about current games, scores, or what's happening right now in the NFL. Returns game IDs that can be used with get_play_by_play.",
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
            },
            {
                "name": "get_play_by_play",
                "description": "Gets detailed play-by-play data for a specific NFL game including scoring plays, drive summaries, box score stats, and player performance. Use this when the user asks about what happened in a specific game, scoring details, drive information, or player stats from a particular game. You can get game_id from the get_live_scores tool.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "game_id": {
                            "type": "string",
                            "description": "The ESPN game ID (e.g., '401547417'). Get this from the get_live_scores tool first by looking at recent games."
                        }
                    },
                    "required": ["game_id"]
                }
            },
            {
                "name": "get_injury_report",
                "description": "Gets information about NFL injury reports and provides guidance on where to find the most current injury data. Use this when users ask about injuries, injury status, who's hurt, availability reports, or practice participation status. Optionally specify a team name for team-specific guidance.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "team_name": {
                            "type": "string",
                            "description": "Optional: The name of the NFL team (e.g., 'Chiefs', 'Patriots', 'Cowboys') for team-specific injury report guidance"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_nfl_news",
                "description": "Gets latest NFL news, trade rumors, and breaking stories. Use this when users ask about NFL news, trades, rumors, signings, or what's happening around the league. Returns recent headlines with summaries.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of news items to return (default 10, max 20)",
                            "default": 10
                        }
                    },
                    "required": []
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
            elif tool_name == "get_play_by_play":
                tool_result = self.get_play_by_play(tool_input["game_id"])
            elif tool_name == "get_injury_report":
                team_name = tool_input.get("team_name", None)
                tool_result = self.get_injury_report(team_name)
            elif tool_name == "get_nfl_news":
                limit = tool_input.get("limit", 10)
                tool_result = self.get_nfl_news(min(limit, 20))
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
            
            # Get conversation record
            conversation = get_or_create_conversation(current_user.id)
            
            # Check if this is a fantasy football question
            fantasy_keywords = ['fantasy', 'my team', 'my roster', 'trade', 'waiver', 'start', 'sit', 'bench', 'draft']
            is_fantasy_question = any(keyword in user_message.lower() for keyword in fantasy_keywords)
            
            # Start with empty history each time (no retained context)
            # This keeps API costs low and avoids rate limits
            conversation_history = []
            
            # If fantasy football question, prepend fantasy context
            if is_fantasy_question:
                fantasy_context = json.loads(conversation.fantasy_context)
                if fantasy_context.get('my_team') or fantasy_context.get('interested_players') or fantasy_context.get('trade_history'):
                    context_message = "FANTASY FOOTBALL CONTEXT:\n"
                    if fantasy_context.get('my_team'):
                        context_message += f"My Team: {', '.join(fantasy_context['my_team'])}\n"
                    if fantasy_context.get('interested_players'):
                        context_message += f"Players I'm Interested In: {', '.join(fantasy_context['interested_players'])}\n"
                    if fantasy_context.get('trade_history'):
                        context_message += f"Trade History: {'; '.join(fantasy_context['trade_history'])}\n"
                    
                    conversation_history.append({
                        "role": "user",
                        "content": context_message
                    })
                    conversation_history.append({
                        "role": "assistant",
                        "content": "I'll remember your fantasy football context."
                    })
            
            response, updated_history = companion.chat(user_message, conversation_history)
            
            # If fantasy football question, extract and update fantasy context
            if is_fantasy_question:
                try:
                    # Ask AI to extract fantasy football information
                    extract_prompt = f"""Based on this conversation:
User: {user_message}
Assistant: {response}

Extract any fantasy football information mentioned and return ONLY a JSON object with this structure:
{{"my_team": ["player names on my team"], "interested_players": ["players I'm interested in"], "trade_history": ["trade offers mentioned"]}}

Return ONLY the JSON, nothing else."""
                    
                    extract_response = companion.client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1024,
                        messages=[{"role": "user", "content": extract_prompt}]
                    )
                    
                    extract_text = ""
                    for block in extract_response.content:
                        if hasattr(block, "text"):
                            extract_text += block.text
                    
                    # Parse extracted data
                    import re
                    json_match = re.search(r'\{.*\}', extract_text, re.DOTALL)
                    if json_match:
                        new_fantasy_data = json.loads(json_match.group())
                        
                        # Merge with existing fantasy context
                        fantasy_context = json.loads(conversation.fantasy_context)
                        
                        # Add new players to my_team (avoid duplicates)
                        for player in new_fantasy_data.get('my_team', []):
                            if player and player not in fantasy_context['my_team']:
                                fantasy_context['my_team'].append(player)
                        
                        # Add new interested players (avoid duplicates)
                        for player in new_fantasy_data.get('interested_players', []):
                            if player and player not in fantasy_context['interested_players']:
                                fantasy_context['interested_players'].append(player)
                        
                        # Add new trades (keep all)
                        for trade in new_fantasy_data.get('trade_history', []):
                            if trade:
                                fantasy_context['trade_history'].append(trade)
                        
                        # Update database
                        conversation.fantasy_context = json.dumps(fantasy_context)
                        
                except Exception as extract_error:
                    logging.warning(f"Could not extract fantasy context: {extract_error}")
            
            # Save conversation history to database for user's chat history display
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
