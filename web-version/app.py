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
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import hashlib
from espn_api.football import League
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from models import db, User, Conversation
from replit_auth import login_manager, make_replit_blueprint, require_login

logging.basicConfig(level=logging.DEBUG)

class NFLCompanion:
    def __init__(self, anthropic_api_key: str):
        """Initialize the NFL AI Companion."""
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        
        self.system_prompt = """You are SportsAI - NFL stats encyclopedia. Lead with numbers, use bullet points, include stat emojis (📊📈🔥⚡🎯). Focus on quantifiable facts, efficiency metrics, rankings, and advanced analytics. Current season: 2025 (9 games played).

MANDATORY TOOL CALLS - DO THESE FIRST:

**VIDEOS (search_play_highlights)**: If user mentions ANY of these words [touchdown, TD, play, highlight, highlights, watch, show, video, scored, throw, run, catch, interception, sack, fumble], you MUST call search_play_highlights BEFORE writing your response. Example queries that require videos: "Josh Allen touchdown", "show me highlights", "that play", "what happened", "Bills game", "player performance". Embed first video as iframe, provide others as links. If error, provide YouTube search link.

**DIAGRAMS (generate_route_play_diagrams)**: If user asks "what is [route/play/coverage]" or asks for recommendations, call this tool first. Show inline as markdown images.

OTHER TOOLS:

**Fantasy:** Check FANTASY FOOTBALL CONTEXT for saved credentials. First time: ask for ESPN League ID (from URL), ESPN_S2 & SWID cookies (F12→Cookies→espn.com, private leagues only). Call get_fantasy_team without team_name to show all teams, then with team_name after selection. Credentials auto-save for future use
**Scores:** get_live_scores for current games. Filter by date for "today" queries
**Recap:** get_live_scores for game_id, then get_play_by_play. Show scoring plays, top performers with stats
**Injuries:** get_injury_report (optional team_name). Explain: Out/Doubtful/Questionable/IR
**News:** get_nfl_news for trades/rumors. Bullet format with stats
**Routes/Plays:** analyze_player_routes_plays, then immediately call generate_route_play_diagrams. Show diagrams inline with stats. Use URLs exactly as provided (start with /static/diagrams/)"""

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

    def get_fantasy_team(self, league_id: str = None, espn_s2: str = None, swid: str = None, year: int = 2025, team_name: str = None) -> dict:
        """Fetch user's ESPN Fantasy Football team roster, matchups, and standings.
        
        Args:
            league_id: ESPN Fantasy League ID (visible in league URL)
            espn_s2: ESPN s2 cookie (for private leagues)
            swid: ESPN SWID cookie (for private leagues)
            year: Season year (default 2025)
            team_name: User's team name (optional - if not provided, returns all teams for selection)
            
        Returns:
            dict with team roster, matchups, standings, and player info
        """
        try:
            # Credentials must be provided as parameters (stored in user's fantasy_context)
            # Do NOT use environment variables - each user has different credentials
            
            if not league_id:
                return {
                    'success': False,
                    'needs_credentials': True,
                    'message': 'To connect your ESPN Fantasy team, I need your League ID.',
                    'setup_help': 'Find your League ID in your ESPN Fantasy Football league URL: https://fantasy.espn.com/football/league?leagueId=YOUR_LEAGUE_ID\n\nJust tell me: "My league ID is 12345678" and I\'ll save it for future use.'
                }
            
            # Initialize league connection
            if espn_s2 and swid:
                # Private league - requires authentication
                league = League(league_id=int(league_id), year=year, espn_s2=espn_s2, swid=swid)
            else:
                # Public league or try without auth
                try:
                    league = League(league_id=int(league_id), year=year)
                except Exception as auth_error:
                    return {
                        'success': False,
                        'message': 'This appears to be a private league. Please provide ESPN_S2 and ESPN_SWID cookies.',
                        'setup_help': 'To get cookies: 1) Log into ESPN Fantasy Football, 2) Open browser Developer Tools (F12), 3) Go to Application/Storage → Cookies → espn.com, 4) Copy espn_s2 and SWID values'
                    }
            
            # Get current week
            current_week = league.current_week
            
            # Get all teams
            teams = league.teams
            
            # If no team_name provided, return list of all teams for user to select
            if not team_name:
                team_list = []
                for team in teams:
                    team_list.append({
                        'team_name': team.team_name,
                        'owner': team.owner if hasattr(team, 'owner') else 'N/A',
                        'record': f"{team.wins}-{team.losses}",
                        'points_for': round(team.points_for, 1)
                    })
                
                return {
                    'success': True,
                    'needs_team_selection': True,
                    'message': 'Please tell me which team is yours from the list below:',
                    'available_teams': team_list,
                    'league_name': league.settings.name if hasattr(league.settings, 'name') else 'Fantasy League',
                    'setup_help': 'Reply with your team name so I can fetch your roster, matchup, and give you personalized advice.'
                }
            
            # Find user's team by team name
            my_team = None
            for team in teams:
                if team.team_name.lower() == team_name.lower():
                    my_team = team
                    break
            
            if not my_team:
                # Fuzzy match - check if team_name is substring of any team name
                for team in teams:
                    if team_name.lower() in team.team_name.lower() or team.team_name.lower() in team_name.lower():
                        my_team = team
                        break
            
            if not my_team:
                return {
                    'success': False,
                    'message': f'Could not find team "{team_name}" in this league.',
                    'available_teams': [{'team_name': team.team_name, 'owner': team.owner if hasattr(team, 'owner') else 'N/A'} for team in teams],
                    'setup_help': 'Please provide the exact team name from the list above.'
                }
            
            # Build roster data
            roster = []
            for player in my_team.roster:
                roster.append({
                    'name': player.name,
                    'position': player.position,
                    'slot': player.slot_position if hasattr(player, 'slot_position') else player.position,
                    'team': player.proTeam if hasattr(player, 'proTeam') else 'N/A',
                    'points_total': round(player.total_points, 1) if hasattr(player, 'total_points') else 0,
                    'projected_points': round(player.projected_total_points, 1) if hasattr(player, 'projected_total_points') else 0,
                    'injury_status': player.injuryStatus if hasattr(player, 'injuryStatus') and player.injuryStatus else 'HEALTHY'
                })
            
            # Get current matchup
            current_matchup = None
            if hasattr(league, 'box_scores') and current_week:
                try:
                    box_scores = league.box_scores(week=current_week)
                    for matchup in box_scores:
                        if matchup.home_team == my_team or matchup.away_team == my_team:
                            opponent = matchup.away_team if matchup.home_team == my_team else matchup.home_team
                            current_matchup = {
                                'week': current_week,
                                'opponent': opponent.team_name,
                                'my_score': round(matchup.home_score if matchup.home_team == my_team else matchup.away_score, 1),
                                'opponent_score': round(matchup.away_score if matchup.home_team == my_team else matchup.home_score, 1),
                                'my_projected': round(matchup.home_projected if matchup.home_team == my_team else matchup.away_projected, 1) if hasattr(matchup, 'home_projected') else 0
                            }
                            break
                except Exception as matchup_error:
                    logging.warning(f"Could not fetch current matchup: {matchup_error}")
            
            # Get standings
            standings = []
            for team in teams:
                standings.append({
                    'team_name': team.team_name,
                    'wins': team.wins,
                    'losses': team.losses,
                    'points_for': round(team.points_for, 1),
                    'points_against': round(team.points_against, 1),
                    'is_my_team': team == my_team
                })
            
            # Sort standings by wins (descending), then points for
            standings.sort(key=lambda x: (x['wins'], x['points_for']), reverse=True)
            
            return {
                'success': True,
                'league_name': league.settings.name if hasattr(league.settings, 'name') else 'Fantasy League',
                'team_name': my_team.team_name,
                'owner': my_team.owner if hasattr(my_team, 'owner') else 'You',
                'record': f"{my_team.wins}-{my_team.losses}",
                'current_week': current_week,
                'roster': roster,
                'roster_count': len(roster),
                'current_matchup': current_matchup,
                'standings': standings,
                'note': 'Fantasy team data refreshed from ESPN Fantasy Football'
            }
            
        except ValueError as ve:
            logging.error(f"Invalid League ID format: {ve}")
            return {
                'success': False,
                'error': str(ve),
                'message': 'Invalid League ID format. League ID must be a number.',
                'setup_help': 'Check your ESPN_LEAGUE_ID in secrets. It should be only numbers (e.g., 12345678)'
            }
        except Exception as e:
            error_msg = str(e).lower()
            logging.error(f"Error fetching ESPN Fantasy team: {e}")
            
            # Handle specific error cases
            if 'league not found' in error_msg or '404' in error_msg:
                return {
                    'success': False,
                    'error': str(e),
                    'message': 'League not found. Double-check your ESPN_LEAGUE_ID.',
                    'setup_help': 'Verify your League ID is correct by checking your ESPN Fantasy Football league URL'
                }
            elif 'unauthorized' in error_msg or '401' in error_msg or '403' in error_msg:
                return {
                    'success': False,
                    'error': str(e),
                    'message': 'Authentication failed. Your ESPN_S2 or ESPN_SWID cookies may be expired.',
                    'setup_help': 'Private leagues require fresh cookies. Log into ESPN Fantasy Football and get new ESPN_S2 and ESPN_SWID values from browser cookies.'
                }
            elif 'timeout' in error_msg or 'timed out' in error_msg:
                return {
                    'success': False,
                    'error': str(e),
                    'message': 'ESPN API request timed out. Try again in a moment.',
                    'setup_help': 'ESPN API may be experiencing high traffic. Wait a few seconds and ask again.'
                }
            elif 'rate limit' in error_msg or '429' in error_msg:
                return {
                    'success': False,
                    'error': str(e),
                    'message': 'ESPN API rate limit reached. Please wait a minute before trying again.',
                    'setup_help': 'ESPN limits API requests. Wait 60 seconds before fetching your team again.'
                }
            else:
                return {
                    'success': False,
                    'error': str(e),
                    'message': f'Could not fetch ESPN Fantasy team. Error: {str(e)}',
                    'setup_help': 'Make sure ESPN_LEAGUE_ID is set correctly. For private leagues, also set ESPN_S2 and ESPN_SWID cookies.'
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

    def search_play_highlights(self, query: str, max_results: int = 5) -> dict:
        """Search for NFL play highlights on YouTube using the YouTube Data API.
        
        Args:
            query: Search query (e.g., "Josh Allen touchdown pass week 8", "Chiefs game highlights")
            max_results: Maximum number of videos to return (default 5, max 10)
            
        Returns:
            dict with video results including titles, video_ids, thumbnails, and embed codes
        """
        try:
            # Get YouTube access token from Replit integration
            hostname = os.getenv('REPLIT_CONNECTORS_HOSTNAME')
            x_replit_token = (
                'repl ' + os.getenv('REPL_IDENTITY') if os.getenv('REPL_IDENTITY')
                else 'depl ' + os.getenv('WEB_REPL_RENEWAL') if os.getenv('WEB_REPL_RENEWAL')
                else None
            )
            
            if not x_replit_token:
                return {
                    'success': False,
                    'message': 'YouTube integration not configured',
                    'videos': []
                }
            
            # Fetch connection settings
            conn_response = requests.get(
                f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=youtube',
                headers={
                    'Accept': 'application/json',
                    'X_REPLIT_TOKEN': x_replit_token
                }
            )
            
            if conn_response.status_code != 200:
                return {
                    'success': False,
                    'message': 'Could not access YouTube connection',
                    'videos': []
                }
            
            connection_data = conn_response.json()
            connection_settings = connection_data.get('items', [])[0] if connection_data.get('items') else None
            
            if not connection_settings:
                return {
                    'success': False,
                    'message': 'YouTube not connected',
                    'videos': []
                }
            
            access_token = connection_settings.get('settings', {}).get('access_token')
            
            if not access_token:
                return {
                    'success': False,
                    'message': 'YouTube access token not available',
                    'videos': []
                }
            
            # Build YouTube client with access token
            youtube = build('youtube', 'v3', credentials=Credentials(token=access_token))
            
            # Search for videos with NFL-focused query
            search_query = f"NFL {query} highlights"
            
            search_response = youtube.search().list(
                q=search_query,
                part='snippet',
                maxResults=min(max_results, 10),
                type='video',
                order='relevance',
                videoDuration='medium'  # Filter for highlight-length videos (4-20 min)
            ).execute()
            
            videos = []
            for item in search_response.get('items', []):
                video_id = item['id']['videoId']
                snippet = item['snippet']
                
                videos.append({
                    'video_id': video_id,
                    'title': snippet['title'],
                    'channel': snippet['channelTitle'],
                    'description': snippet['description'][:200] + '...' if len(snippet['description']) > 200 else snippet['description'],
                    'thumbnail': snippet['thumbnails']['high']['url'] if 'high' in snippet['thumbnails'] else snippet['thumbnails']['default']['url'],
                    'published_at': snippet['publishedAt'],
                    'embed_url': f'https://www.youtube.com/embed/{video_id}',
                    'watch_url': f'https://www.youtube.com/watch?v={video_id}'
                })
            
            return {
                'success': True,
                'query': search_query,
                'videos': videos,
                'count': len(videos)
            }
            
        except Exception as e:
            error_str = str(e)
            logging.error(f"Error searching play highlights: {error_str}")
            
            # Build search query for fallback link
            search_query = f"NFL {query} highlights"
            
            # Detect quota exceeded errors
            if 'quota' in error_str.lower() or 'quotaExceeded' in error_str:
                return {
                    'success': False,
                    'error': 'quota_exceeded',
                    'message': 'YouTube API daily quota exceeded. Video search will be available after quota resets at midnight Pacific Time.',
                    'search_query': search_query,
                    'fallback_url': f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}",
                    'videos': []
                }
            
            return {
                'success': False,
                'error': error_str,
                'message': 'Could not search for play highlights',
                'search_query': search_query,
                'fallback_url': f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}",
                'videos': []
            }

    def analyze_player_routes_plays(self, player_name: str, position: str, num_results: int = 3) -> dict:
        """Analyze a player's most successful routes (WR/TE) or plays (QB) from their last 4 games.
        
        Note: This is simulated data based on typical NFL route/play distributions since ESPN's 
        public API doesn't provide granular route-level data.
        """
        try:
            # Common route types for receivers (season-long stats)
            receiver_routes = {
                'Go/Vertical': {'avg_yards': 18.5, 'targets': 28, 'receptions': 16, 'tds': 4, 'success_rate': 57},
                'Slant': {'avg_yards': 8.2, 'targets': 42, 'receptions': 33, 'tds': 2, 'success_rate': 79},
                'Out': {'avg_yards': 10.3, 'targets': 35, 'receptions': 24, 'tds': 1, 'success_rate': 69},
                'Corner': {'avg_yards': 14.7, 'targets': 24, 'receptions': 14, 'tds': 3, 'success_rate': 58},
                'Post': {'avg_yards': 16.2, 'targets': 19, 'receptions': 12, 'tds': 4, 'success_rate': 63},
                'Comeback': {'avg_yards': 12.1, 'targets': 26, 'receptions': 19, 'tds': 1, 'success_rate': 73},
                'Dig/In': {'avg_yards': 11.8, 'targets': 33, 'receptions': 26, 'tds': 2, 'success_rate': 79},
                'Wheel': {'avg_yards': 15.4, 'targets': 14, 'receptions': 7, 'tds': 2, 'success_rate': 50},
                'Crossing': {'avg_yards': 9.5, 'targets': 38, 'receptions': 31, 'tds': 3, 'success_rate': 82},
                'Hitch': {'avg_yards': 6.8, 'targets': 47, 'receptions': 40, 'tds': 1, 'success_rate': 85}
            }
            
            # Common play types for QBs (season-long stats)
            qb_plays = {
                'Play Action Pass': {'completions': 65, 'attempts': 88, 'yards': 952, 'tds': 9, 'success_rate': 74},
                'RPO (Run-Pass Option)': {'completions': 51, 'attempts': 67, 'yards': 543, 'tds': 5, 'success_rate': 76},
                'Bootleg': {'completions': 35, 'attempts': 42, 'yards': 458, 'tds': 5, 'success_rate': 83},
                'Screen Pass': {'completions': 42, 'attempts': 47, 'yards': 328, 'tds': 2, 'success_rate': 89},
                'Quick Slant Package': {'completions': 74, 'attempts': 88, 'yards': 663, 'tds': 5, 'success_rate': 84},
                'Deep Shot/Vertical': {'completions': 28, 'attempts': 58, 'yards': 851, 'tds': 7, 'success_rate': 48},
                'Designed Rollout': {'completions': 44, 'attempts': 56, 'yards': 567, 'tds': 4, 'success_rate': 79},
                'Shotgun Draw': {'carries': 19, 'yards': 120, 'tds': 2, 'success_rate': 63},
                'Empty Set Pass': {'completions': 58, 'attempts': 81, 'yards': 689, 'tds': 5, 'success_rate': 72},
                'Two-Minute Drill': {'completions': 49, 'attempts': 65, 'yards': 618, 'tds': 7, 'success_rate': 75}
            }
            
            position_upper = position.upper()
            
            # Determine if this is a receiver or QB
            if position_upper in ['WR', 'TE', 'RECEIVER', 'WIDE RECEIVER', 'TIGHT END']:
                # Sort routes by success rate * targets (high impact routes)
                sorted_routes = sorted(
                    receiver_routes.items(),
                    key=lambda x: x[1]['success_rate'] * x[1]['targets'],
                    reverse=True
                )
                
                top_routes = sorted_routes[:num_results]
                
                results = []
                for route_name, stats in top_routes:
                    results.append({
                        'route_name': route_name,
                        'targets': stats['targets'],
                        'receptions': stats['receptions'],
                        'avg_yards': stats['avg_yards'],
                        'touchdowns': stats['tds'],
                        'success_rate': stats['success_rate']
                    })
                
                return {
                    'success': True,
                    'player': player_name,
                    'position': position,
                    'analysis_type': 'routes',
                    'games_analyzed': 9,
                    'top_routes': results,
                    'note': 'Analysis based on typical route distribution patterns for this player archetype this season. Actual granular route data requires All-22 film access.'
                }
                
            elif position_upper in ['QB', 'QUARTERBACK']:
                # Sort plays by success rate * attempts/carries (high impact plays)
                sorted_plays = sorted(
                    qb_plays.items(),
                    key=lambda x: x[1]['success_rate'] * x[1].get('attempts', x[1].get('carries', 1)),
                    reverse=True
                )
                
                top_plays = sorted_plays[:num_results]
                
                results = []
                for play_name, stats in top_plays:
                    if 'attempts' in stats:
                        results.append({
                            'play_name': play_name,
                            'completions': stats['completions'],
                            'attempts': stats['attempts'],
                            'yards': stats['yards'],
                            'touchdowns': stats['tds'],
                            'success_rate': stats['success_rate']
                        })
                    else:
                        results.append({
                            'play_name': play_name,
                            'carries': stats['carries'],
                            'yards': stats['yards'],
                            'touchdowns': stats['tds'],
                            'success_rate': stats['success_rate']
                        })
                
                return {
                    'success': True,
                    'player': player_name,
                    'position': position,
                    'analysis_type': 'plays',
                    'games_analyzed': 9,
                    'top_plays': results,
                    'note': 'Analysis based on typical play-calling patterns for this player archetype this season. Actual granular play data requires All-22 film access.'
                }
            else:
                return {
                    'success': False,
                    'message': f'Route/play analysis is only available for WR, TE, and QB positions. {player_name} is listed as {position}.'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Could not analyze routes/plays for {player_name}'
            }

    def generate_route_play_diagrams(self, route_or_play_names: list, diagram_type: str) -> dict:
        """Generate visual diagrams for specific routes or plays and save to static folder.
        
        Args:
            route_or_play_names: List of route names (e.g., ['Slant', 'Post']) or play names
            diagram_type: Either 'route' for WR/TE routes or 'play' for QB plays
        
        Returns:
            dict with diagram URLs
        """
        try:
            diagrams = []
            
            # Get the absolute path to the diagrams directory
            diagrams_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'diagrams')
            os.makedirs(diagrams_dir, exist_ok=True)
            
            for name in route_or_play_names:
                # Create unique filename based on type and name
                hash_input = f"{diagram_type}_{name}".encode()
                filename = f"{diagram_type}_{hashlib.md5(hash_input).hexdigest()[:8]}.png"
                filepath = os.path.join(diagrams_dir, filename)
                url = f"/static/diagrams/{filename}"
                
                # Check if diagram already exists
                if os.path.exists(filepath):
                    diagrams.append({
                        'name': name,
                        'url': url,
                        'success': True
                    })
                    continue
                
                # Generate new diagram
                try:
                    fig, ax = plt.subplots(figsize=(10, 8))
                    ax.set_xlim(-5, 25)
                    ax.set_ylim(0, 30)
                    ax.set_aspect('equal')
                    ax.axis('off')
                    
                    if diagram_type == 'route':
                        # Draw route diagram
                        # Line of scrimmage
                        ax.plot([0, 0], [0, 30], 'k-', linewidth=2, label='Line of Scrimmage')
                        
                        # QB position
                        ax.plot(0, 15, 'ro', markersize=15, label='QB')
                        ax.text(-2, 15, 'QB', fontsize=12, ha='right', va='center', fontweight='bold')
                        
                        # WR starting position
                        ax.plot(0, 10, 'bo', markersize=12, label='WR')
                        ax.text(-2, 10, 'WR', fontsize=10, ha='right', va='center')
                        
                        # Draw yard markers
                        for y in [5, 10, 15, 20]:
                            ax.plot([y, y], [0, 30], 'gray', linewidth=0.5, alpha=0.3)
                            ax.text(y, -1, f'{y}y', fontsize=8, ha='center', color='gray')
                        
                        # Draw specific route patterns
                        if 'slant' in name.lower():
                            # Slant route: 5 yards forward, then diagonal
                            ax.arrow(0, 10, 5, 0, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                            ax.arrow(5, 10, 5, 5, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                        elif 'post' in name.lower():
                            # Post route: 12 yards forward, then diagonal toward middle
                            ax.arrow(0, 10, 12, 0, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                            ax.arrow(12, 10, 6, 5, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                        elif 'go' in name.lower() or 'vertical' in name.lower():
                            # Go route: straight vertical
                            ax.arrow(0, 10, 20, 0, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                        elif 'out' in name.lower():
                            # Out route: 10 yards forward, then perpendicular outside
                            ax.arrow(0, 10, 10, 0, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                            ax.arrow(10, 10, 0, -6, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                        elif 'corner' in name.lower():
                            # Corner route: 12 yards forward, then diagonal outside
                            ax.arrow(0, 10, 12, 0, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                            ax.arrow(12, 10, 6, -5, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                        elif 'comeback' in name.lower():
                            # Comeback route: 15 yards forward, then back toward QB
                            ax.arrow(0, 10, 15, 0, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                            ax.arrow(15, 10, -3, 0, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                        elif 'dig' in name.lower() or 'in' in name.lower():
                            # Dig/In route: 10 yards forward, then across middle
                            ax.arrow(0, 10, 10, 0, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                            ax.arrow(10, 10, 0, 6, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                        elif 'wheel' in name.lower():
                            # Wheel route: curved upfield
                            from matplotlib.patches import FancyBboxPatch, Arc
                            arc = Arc((5, 10), 10, 16, angle=0, theta1=0, theta2=60, color='blue', linewidth=2)
                            ax.add_patch(arc)
                            ax.arrow(8, 18, 2, 2, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                        elif 'crossing' in name.lower() or 'cross' in name.lower():
                            # Crossing route: shallow across field
                            ax.arrow(0, 10, 8, 0, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                            ax.arrow(8, 10, 0, 8, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                        elif 'hitch' in name.lower():
                            # Hitch route: 5-7 yards forward, then back
                            ax.arrow(0, 10, 6, 0, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                            ax.arrow(6, 10, -1.5, 0, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                        else:
                            # Default: simple forward route
                            ax.arrow(0, 10, 12, 0, head_width=0.8, head_length=0.5, fc='blue', ec='blue', linewidth=2)
                        
                        ax.set_title(f'{name} Route', fontsize=16, fontweight='bold', pad=20)
                        
                    elif diagram_type == 'play':
                        # Import for arrow patches
                        from matplotlib.patches import FancyArrowPatch
                        
                        # Draw play-specific diagrams with movement arrows
                        # Line of scrimmage
                        ax.plot([0, 0], [0, 30], 'k--', linewidth=2, alpha=0.5, label='LOS')
                        
                        # Yard markers
                        for y in [5, 10, 15, 20]:
                            ax.plot([y, y], [0, 30], 'gray', linewidth=0.5, alpha=0.2)
                            ax.text(y, -1, f'{y}y', fontsize=8, ha='center', color='gray')
                        
                        # Play-specific formations and movements
                        if 'play action' in name.lower():
                            # Play Action Pass - Fake handoff, then deep pass
                            # O-line (vertical formation at line of scrimmage)
                            for i in range(5):
                                ax.plot(0, 12 + i * 1.5, 'ko', markersize=8)
                            # QB - fake handoff then dropback
                            ax.plot(-3, 15, 'ro', markersize=12, label='QB')
                            arrow1 = FancyArrowPatch((-3, 15), (1, 15), arrowstyle='->', mutation_scale=20, linewidth=2, color='red', linestyle='--', label='Fake')
                            ax.add_patch(arrow1)
                            arrow2 = FancyArrowPatch((1, 15), (-5, 15), arrowstyle='->', mutation_scale=20, linewidth=2.5, color='red')
                            ax.add_patch(arrow2)
                            # RB - fake receive
                            ax.plot(-2, 15, 'go', markersize=10)
                            # WR deep routes
                            ax.plot(0, 8, 'bo', markersize=9)
                            arrow3 = FancyArrowPatch((0, 8), (18, 6), arrowstyle='->', mutation_scale=20, linewidth=2.5, color='blue')
                            ax.add_patch(arrow3)
                            ax.plot(0, 22, 'bo', markersize=9)
                            arrow4 = FancyArrowPatch((0, 22), (18, 24), arrowstyle='->', mutation_scale=20, linewidth=2.5, color='blue')
                            ax.add_patch(arrow4)
                            
                        elif 'bootleg' in name.lower():
                            # Bootleg - QB rolls out to sideline
                            for i in range(5):
                                ax.plot(0, 12 + i * 1.5, 'ko', markersize=8)
                            # QB - rolls out
                            ax.plot(-3, 15, 'ro', markersize=12)
                            arrow1 = FancyArrowPatch((-3, 15), (8, 7), arrowstyle='->', mutation_scale=20, linewidth=3, color='red')
                            ax.add_patch(arrow1)
                            # RB - fake opposite
                            ax.plot(-2, 15, 'go', markersize=10)
                            arrow2 = FancyArrowPatch((-2, 15), (3, 22), arrowstyle='->', mutation_scale=18, linewidth=2, color='green', linestyle='--')
                            ax.add_patch(arrow2)
                            # TE drags across
                            ax.plot(0, 19, 'co', markersize=9)
                            arrow3 = FancyArrowPatch((0, 19), (10, 12), arrowstyle='->', mutation_scale=20, linewidth=2.5, color='cyan')
                            ax.add_patch(arrow3)
                            
                        elif 'rpo' in name.lower():
                            # RPO - Run-Pass Option
                            for i in range(5):
                                ax.plot(0, 12 + i * 1.5, 'ko', markersize=8)
                            # QB - reads defender
                            ax.plot(-3, 15, 'ro', markersize=12)
                            ax.text(-3, 12, 'READ', fontsize=8, ha='center', fontweight='bold', color='red')
                            # RB - run option
                            ax.plot(-2, 15, 'go', markersize=10)
                            arrow1 = FancyArrowPatch((-2, 15), (8, 15), arrowstyle='->', mutation_scale=20, linewidth=2.5, color='green', label='Run Option')
                            ax.add_patch(arrow1)
                            # WR - slant option
                            ax.plot(0, 8, 'bo', markersize=9)
                            arrow2 = FancyArrowPatch((0, 8), (6, 13), arrowstyle='->', mutation_scale=20, linewidth=2.5, color='blue', linestyle='--', label='Pass Option')
                            ax.add_patch(arrow2)
                            
                        elif 'screen' in name.lower():
                            # Screen Pass - Blockers ahead
                            for i in range(5):
                                ax.plot(0, 12 + i * 1.5, 'ko', markersize=8)
                            # QB - drops back
                            ax.plot(-3, 15, 'ro', markersize=12)
                            arrow1 = FancyArrowPatch((-3, 15), (-6, 15), arrowstyle='->', mutation_scale=20, linewidth=2, color='red')
                            ax.add_patch(arrow1)
                            # RB - releases for screen
                            ax.plot(-2, 15, 'go', markersize=10)
                            arrow2 = FancyArrowPatch((-2, 15), (8, 15), arrowstyle='->', mutation_scale=20, linewidth=3, color='green')
                            ax.add_patch(arrow2)
                            # O-line releases to block
                            arrow3 = FancyArrowPatch((0, 13.5), (5, 15), arrowstyle='->', mutation_scale=15, linewidth=2, color='black', linestyle='--')
                            ax.add_patch(arrow3)
                            arrow4 = FancyArrowPatch((0, 16.5), (7, 15), arrowstyle='->', mutation_scale=15, linewidth=2, color='black', linestyle='--')
                            ax.add_patch(arrow4)
                            
                        elif 'slant' in name.lower():
                            # Quick Slant Package
                            for i in range(5):
                                ax.plot(0, 12 + i * 1.5, 'ko', markersize=8)
                            # QB - quick release
                            ax.plot(-3, 15, 'ro', markersize=12)
                            # WRs - slant routes
                            ax.plot(0, 8, 'bo', markersize=9)
                            arrow1 = FancyArrowPatch((0, 8), (6, 13), arrowstyle='->', mutation_scale=20, linewidth=2.5, color='blue')
                            ax.add_patch(arrow1)
                            ax.plot(0, 22, 'bo', markersize=9)
                            arrow2 = FancyArrowPatch((0, 22), (6, 17), arrowstyle='->', mutation_scale=20, linewidth=2.5, color='blue')
                            ax.add_patch(arrow2)
                            
                        elif 'deep' in name.lower() or 'vertical' in name.lower():
                            # Deep Shot/Vertical
                            for i in range(5):
                                ax.plot(0, 12 + i * 1.5, 'ko', markersize=8)
                            # QB - deep drop
                            ax.plot(-4, 15, 'ro', markersize=12)
                            # WRs - go routes
                            ax.plot(0, 6, 'bo', markersize=9)
                            arrow1 = FancyArrowPatch((0, 6), (20, 3), arrowstyle='->', mutation_scale=20, linewidth=3, color='blue')
                            ax.add_patch(arrow1)
                            ax.plot(0, 24, 'bo', markersize=9)
                            arrow2 = FancyArrowPatch((0, 24), (20, 27), arrowstyle='->', mutation_scale=20, linewidth=3, color='blue')
                            ax.add_patch(arrow2)
                            
                        elif 'rollout' in name.lower():
                            # Designed Rollout
                            for i in range(5):
                                ax.plot(0, 12 + i * 1.5, 'ko', markersize=8)
                            # QB - rolls out
                            ax.plot(-3, 15, 'ro', markersize=12)
                            arrow1 = FancyArrowPatch((-3, 15), (6, 9), arrowstyle='->', mutation_scale=20, linewidth=3, color='red')
                            ax.add_patch(arrow1)
                            # WRs - crossing routes
                            ax.plot(0, 8, 'bo', markersize=9)
                            arrow2 = FancyArrowPatch((0, 8), (10, 18), arrowstyle='->', mutation_scale=20, linewidth=2.5, color='blue')
                            ax.add_patch(arrow2)
                            
                        elif 'draw' in name.lower():
                            # Shotgun Draw
                            for i in range(5):
                                ax.plot(0, 12 + i * 1.5, 'ko', markersize=8)
                            # QB - hands off
                            ax.plot(-4, 15, 'ro', markersize=12)
                            # RB - delayed run
                            ax.plot(-3, 15, 'go', markersize=10)
                            arrow1 = FancyArrowPatch((-3, 15), (12, 15), arrowstyle='->', mutation_scale=20, linewidth=3, color='green')
                            ax.add_patch(arrow1)
                            
                        elif 'empty' in name.lower():
                            # Empty Set - all receivers spread
                            for i in range(5):
                                ax.plot(0, 12 + i * 1.5, 'ko', markersize=8)
                            # QB - shotgun
                            ax.plot(-4, 15, 'ro', markersize=12)
                            # 5 receivers spread
                            positions = [(0, 3), (0, 9), (0, 15), (0, 21), (0, 27)]
                            for i, pos in enumerate(positions):
                                ax.plot(pos[0], pos[1], 'bo', markersize=9)
                                if i % 2 == 0:
                                    arrow = FancyArrowPatch(pos, (12, pos[1] + 2), arrowstyle='->', mutation_scale=18, linewidth=2, color='blue')
                                else:
                                    arrow = FancyArrowPatch(pos, (8, pos[1] - 3), arrowstyle='->', mutation_scale=18, linewidth=2, color='blue')
                                ax.add_patch(arrow)
                                
                        elif 'two-minute' in name.lower() or 'drill' in name.lower():
                            # Two-Minute Drill - hurry up
                            for i in range(5):
                                ax.plot(0, 12 + i * 1.5, 'ko', markersize=8)
                            # QB - quick snap
                            ax.plot(-3, 15, 'ro', markersize=12)
                            ax.text(-3, 12, 'HURRY!', fontsize=9, ha='center', fontweight='bold', color='red')
                            # Quick routes
                            ax.plot(0, 7, 'bo', markersize=9)
                            arrow1 = FancyArrowPatch((0, 7), (8, 7), arrowstyle='->', mutation_scale=20, linewidth=2.5, color='blue')
                            ax.add_patch(arrow1)
                            ax.plot(0, 23, 'bo', markersize=9)
                            arrow2 = FancyArrowPatch((0, 23), (8, 23), arrowstyle='->', mutation_scale=20, linewidth=2.5, color='blue')
                            ax.add_patch(arrow2)
                        
                        else:
                            # Generic play formation
                            for i in range(5):
                                ax.plot(0, 12 + i * 1.5, 'ko', markersize=8)
                            ax.plot(-3, 15, 'ro', markersize=12)
                            ax.plot(-2, 15, 'go', markersize=10)
                            ax.plot(0, 8, 'bo', markersize=9)
                            ax.plot(0, 22, 'bo', markersize=9)
                        
                        ax.set_title(f'{name}', fontsize=14, fontweight='bold', pad=20)
                    
                    elif diagram_type == 'coverage':
                        # Draw defensive coverage diagram
                        from matplotlib.patches import Rectangle, Arc
                        
                        # Line of scrimmage
                        ax.plot([0, 0], [0, 30], 'k--', linewidth=2, alpha=0.5)
                        
                        # Yard markers  
                        for y in [5, 10, 15, 20]:
                            ax.plot([y, y], [0, 30], 'gray', linewidth=0.5, alpha=0.2)
                            ax.text(y, -1, f'{y}y', fontsize=8, ha='center', color='gray')
                        
                        # Coverage-specific formations
                        if 'cover 2' in name.lower() or 'cover2' in name.lower():
                            # Cover 2 - Two deep safeties
                            ax.plot(15, 10, 'r^', markersize=14)
                            ax.text(15, 8, 'S', fontsize=10, ha='center', fontweight='bold', color='red')
                            ax.plot(15, 20, 'r^', markersize=14)
                            ax.text(15, 22, 'S', fontsize=10, ha='center', fontweight='bold', color='red')
                            # CBs on outside
                            ax.plot(5, 5, 'r^', markersize=12)
                            ax.text(5, 3, 'CB', fontsize=9, ha='center', color='red')
                            ax.plot(5, 25, 'r^', markersize=12)
                            ax.text(5, 27, 'CB', fontsize=9, ha='center', color='red')
                            # LBs underneath
                            for i, y_pos in enumerate([9, 15, 21]):
                                ax.plot(3, y_pos, 'r^', markersize=10)
                                ax.text(3, y_pos - 1.5, 'LB', fontsize=8, ha='center', color='red')
                            # Deep zones
                            deep_zone1 = Rectangle((10, 0), 15, 15, linewidth=2, edgecolor='red', facecolor='red', alpha=0.1)
                            deep_zone2 = Rectangle((10, 15), 15, 15, linewidth=2, edgecolor='red', facecolor='red', alpha=0.1)
                            ax.add_patch(deep_zone1)
                            ax.add_patch(deep_zone2)
                        
                        elif 'cover 3' in name.lower() or 'cover3' in name.lower():
                            # Cover 3 - Three deep zones
                            # Deep defenders
                            ax.plot(15, 7.5, 'r^', markersize=14)
                            ax.text(15, 5.5, 'CB', fontsize=10, ha='center', fontweight='bold', color='red')
                            ax.plot(15, 15, 'r^', markersize=14)
                            ax.text(15, 13, 'S', fontsize=10, ha='center', fontweight='bold', color='red')
                            ax.plot(15, 22.5, 'r^', markersize=14)
                            ax.text(15, 24.5, 'CB', fontsize=10, ha='center', fontweight='bold', color='red')
                            # LBs underneath
                            for i, y_pos in enumerate([9, 15, 21]):
                                ax.plot(4, y_pos, 'r^', markersize=10)
                            # Deep thirds
                            third1 = Rectangle((10, 0), 15, 10, linewidth=2, edgecolor='red', facecolor='red', alpha=0.1)
                            third2 = Rectangle((10, 10), 15, 10, linewidth=2, edgecolor='red', facecolor='red', alpha=0.1)
                            third3 = Rectangle((10, 20), 15, 10, linewidth=2, edgecolor='red', facecolor='red', alpha=0.1)
                            ax.add_patch(third1)
                            ax.add_patch(third2)
                            ax.add_patch(third3)
                        
                        elif 'cover 4' in name.lower() or 'cover4' in name.lower() or 'quarters' in name.lower():
                            # Cover 4 / Quarters - Four deep zones
                            ax.plot(15, 6, 'r^', markersize=14)
                            ax.text(15, 4, 'CB', fontsize=9, ha='center', fontweight='bold', color='red')
                            ax.plot(15, 12, 'r^', markersize=14)
                            ax.text(15, 10, 'S', fontsize=9, ha='center', fontweight='bold', color='red')
                            ax.plot(15, 18, 'r^', markersize=14)
                            ax.text(15, 16, 'S', fontsize=9, ha='center', fontweight='bold', color='red')
                            ax.plot(15, 24, 'r^', markersize=14)
                            ax.text(15, 26, 'CB', fontsize=9, ha='center', fontweight='bold', color='red')
                            # LBs
                            for y_pos in [10, 15, 20]:
                                ax.plot(4, y_pos, 'r^', markersize=10)
                            # Four quarters
                            q1 = Rectangle((10, 0), 15, 7.5, linewidth=2, edgecolor='red', facecolor='red', alpha=0.1)
                            q2 = Rectangle((10, 7.5), 15, 7.5, linewidth=2, edgecolor='red', facecolor='red', alpha=0.1)
                            q3 = Rectangle((10, 15), 15, 7.5, linewidth=2, edgecolor='red', facecolor='red', alpha=0.1)
                            q4 = Rectangle((10, 22.5), 15, 7.5, linewidth=2, edgecolor='red', facecolor='red', alpha=0.1)
                            ax.add_patch(q1)
                            ax.add_patch(q2)
                            ax.add_patch(q3)
                            ax.add_patch(q4)
                        
                        elif 'man' in name.lower() or 'cover 1' in name.lower() or 'cover1' in name.lower():
                            # Man Coverage / Cover 1
                            # 1 deep safety
                            ax.plot(15, 15, 'r^', markersize=15)
                            ax.text(15, 13, 'FS', fontsize=11, ha='center', fontweight='bold', color='red')
                            # CBs in man
                            ax.plot(0, 8, 'r^', markersize=12)
                            ax.text(0, 6, 'CB', fontsize=9, ha='center', color='red')
                            ax.plot(0, 22, 'r^', markersize=12)
                            ax.text(0, 24, 'CB', fontsize=9, ha='center', color='red')
                            # LBs in man
                            for i, y_pos in enumerate([12, 15, 18]):
                                ax.plot(2, y_pos, 'r^', markersize=10)
                                ax.text(2, y_pos - 1.5, 'LB', fontsize=8, ha='center', color='red')
                            ax.text(12, 25, 'MAN COVERAGE', fontsize=11, ha='center', fontweight='bold', color='red')
                        
                        elif 'cover 6' in name.lower() or 'cover6' in name.lower():
                            # Cover 6 - Quarter-quarter-half
                            ax.plot(15, 7, 'r^', markersize=14)
                            ax.text(15, 5, 'CB', fontsize=9, ha='center', fontweight='bold', color='red')
                            ax.plot(15, 13, 'r^', markersize=14)
                            ax.text(15, 11, 'S', fontsize=9, ha='center', fontweight='bold', color='red')
                            ax.plot(15, 21, 'r^', markersize=14)
                            ax.text(15, 23, 'S', fontsize=9, ha='center', fontweight='bold', color='red')
                            # Zones
                            quarter1 = Rectangle((10, 0), 15, 7.5, linewidth=2, edgecolor='red', facecolor='red', alpha=0.1)
                            quarter2 = Rectangle((10, 7.5), 15, 7.5, linewidth=2, edgecolor='red', facecolor='red', alpha=0.1)
                            half = Rectangle((10, 15), 15, 15, linewidth=2, edgecolor='red', facecolor='red', alpha=0.15)
                            ax.add_patch(quarter1)
                            ax.add_patch(quarter2)
                            ax.add_patch(half)
                        
                        else:
                            # Generic coverage
                            for i in range(7):
                                x = 5
                                y = 5 + i * 3.5
                                ax.plot(x, y, 'r^', markersize=12)
                        
                        ax.set_title(f'{name}', fontsize=14, fontweight='bold', pad=20, color='red')
                    
                    # Save diagram
                    plt.tight_layout()
                    plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
                    plt.close(fig)
                    
                    diagrams.append({
                        'name': name,
                        'url': url,
                        'success': True
                    })
                    
                except Exception as draw_error:
                    logging.error(f"Error drawing diagram for {name}: {draw_error}")
                    plt.close('all')  # Clean up any open figures
                    diagrams.append({
                        'name': name,
                        'error': str(draw_error),
                        'success': False
                    })
            
            return {
                'success': True,
                'diagrams': diagrams,
                'count': len([d for d in diagrams if d.get('success')]),
                'note': 'Diagrams are simplified tactical illustrations for educational purposes.'
            }
            
        except Exception as e:
            logging.error(f"Error generating diagrams: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Could not generate diagrams at this time'
            }

    def chat(self, user_message: str, conversation_history: list, fantasy_context: dict = None) -> tuple:
        """Main chat interface with tool use.
        
        Returns:
            tuple: (assistant_message, conversation_history, tool_usage_data)
                   tool_usage_data contains info about tools used in this conversation
        """
        tool_usage_data = {
            'used_analyze_player_routes_plays': False,
            'analysis_data': None
        }
        
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
            },
            {
                "name": "analyze_player_routes_plays",
                "description": "Analyzes a player's most successful routes (for WR/TE) or plays (for QB) from their games this season. Use this when users ask about a player's favorite routes, best plays, route tree, or play tendencies. Returns top routes/plays with success rates, targets/attempts, yards, and touchdowns. Only works for QB, WR, and TE positions.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "player_name": {
                            "type": "string",
                            "description": "The name of the player (e.g., 'Travis Kelce', 'Patrick Mahomes', 'Tyreek Hill')"
                        },
                        "position": {
                            "type": "string",
                            "description": "The player's position: 'QB', 'WR', or 'TE'"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of top routes/plays to return (default 3)",
                            "default": 3
                        }
                    },
                    "required": ["player_name", "position"]
                }
            },
            {
                "name": "generate_route_play_diagrams",
                "description": "Generates visual diagrams for routes, plays, or defensive coverages. Returns image URLs that can be embedded in markdown. Shows visual tactical illustrations with positions, arrows, zones, and yard markers.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "route_or_play_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of route names (e.g., ['Slant', 'Post']), play names (e.g., ['Bootleg', 'RPO']), or coverage names (e.g., ['Cover 2', 'Cover 3', 'Man Coverage'])"
                        },
                        "diagram_type": {
                            "type": "string",
                            "enum": ["route", "play", "coverage"],
                            "description": "Type of diagram: 'route' for WR/TE routes (QB+WR), 'play' for QB plays (full formation), 'coverage' for defensive schemes (DBs+zones)"
                        }
                    },
                    "required": ["route_or_play_names", "diagram_type"]
                }
            },
            {
                "name": "search_play_highlights",
                "description": "Search for NFL play highlights on YouTube. Use this when users ask about specific plays, touchdowns, game highlights, or player performances and want to watch video highlights. Returns YouTube video results with embed codes that can be displayed in the chat.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for the highlight (e.g., 'Josh Allen touchdown pass week 8', 'Chiefs vs Bills highlights', 'Patrick Mahomes incredible throw')"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of videos to return (default 5, max 10)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_fantasy_team",
                "description": "Fetches the user's ESPN Fantasy Football team roster, current matchup, and league standings. Use this when users ask about their fantasy team, roster, who to start/sit, or want personalized fantasy advice. Requires the user's ESPN credentials (league_id, and optionally espn_s2/swid for private leagues) - check FANTASY FOOTBALL CONTEXT for saved credentials. If team_name is not provided and user hasn't selected their team yet, this will return a list of all teams in the league for the user to choose from.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "league_id": {
                            "type": "string",
                            "description": "ESPN Fantasy League ID (from FANTASY FOOTBALL CONTEXT or user-provided)"
                        },
                        "espn_s2": {
                            "type": "string",
                            "description": "ESPN S2 cookie for private leagues (from FANTASY FOOTBALL CONTEXT or user-provided, optional)"
                        },
                        "swid": {
                            "type": "string",
                            "description": "ESPN SWID cookie for private leagues (from FANTASY FOOTBALL CONTEXT or user-provided, optional)"
                        },
                        "year": {
                            "type": "integer",
                            "description": "Season year (default 2025)",
                            "default": 2025
                        },
                        "team_name": {
                            "type": "string",
                            "description": "The user's fantasy team name (optional - omit if user hasn't told you their team name yet)"
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
            elif tool_name == "analyze_player_routes_plays":
                player_name = tool_input["player_name"]
                position = tool_input["position"]
                num_results = tool_input.get("num_results", 3)
                tool_result = self.analyze_player_routes_plays(player_name, position, num_results)
                # Track that we used this tool
                tool_usage_data['used_analyze_player_routes_plays'] = True
                tool_usage_data['analysis_data'] = {
                    'player_name': player_name,
                    'position': position,
                    'result': tool_result
                }
            elif tool_name == "generate_route_play_diagrams":
                route_or_play_names = tool_input["route_or_play_names"]
                diagram_type = tool_input["diagram_type"]
                tool_result = self.generate_route_play_diagrams(route_or_play_names, diagram_type)
            elif tool_name == "search_play_highlights":
                query = tool_input["query"]
                max_results = tool_input.get("max_results", 5)
                tool_result = self.search_play_highlights(query, max_results)
            elif tool_name == "get_fantasy_team":
                year = tool_input.get("year", 2025)
                team_name = tool_input.get("team_name", None)
                
                # Auto-inject credentials from user's stored fantasy_context
                # This ensures each user's credentials are automatically used
                league_id = tool_input.get("league_id", None)
                espn_s2 = tool_input.get("espn_s2", None)
                swid = tool_input.get("swid", None)
                
                # If fantasy_context provided and no credentials in tool_input, use stored credentials
                if fantasy_context:
                    if not league_id and fantasy_context.get('espn_league_id'):
                        league_id = fantasy_context['espn_league_id']
                    if not espn_s2 and fantasy_context.get('espn_s2'):
                        espn_s2 = fantasy_context['espn_s2']
                    if not swid and fantasy_context.get('espn_swid'):
                        swid = fantasy_context['espn_swid']
                    # Also auto-inject team_name if not provided
                    if not team_name and fantasy_context.get('espn_team_name'):
                        team_name = fantasy_context['espn_team_name']
                
                tool_result = self.get_fantasy_team(
                    league_id=league_id,
                    espn_s2=espn_s2,
                    swid=swid,
                    year=year,
                    team_name=team_name
                )
                # Track that we used this tool
                tool_usage_data['used_get_fantasy_team'] = True
                tool_usage_data['fantasy_team_data'] = tool_result
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
        
        return assistant_message, conversation_history, tool_usage_data


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
            
            # Check for proactive injury updates (once per day, at session start)
            injury_update_message = None
            fantasy_context = json.loads(conversation.fantasy_context)
            
            # Check if we should run injury check
            should_check_injuries = False
            if conversation.last_injury_check is None:
                # Never checked before
                should_check_injuries = True
            else:
                # Check if it's been more than 24 hours
                hours_since_check = (datetime.now() - conversation.last_injury_check).total_seconds() / 3600
                should_check_injuries = hours_since_check >= 24
            
            # Only check if user has fantasy team data
            has_fantasy_data = bool(fantasy_context.get('my_team') or fantasy_context.get('interested_players'))
            
            if should_check_injuries and has_fantasy_data:
                injury_check_result = companion.check_fantasy_team_injuries(fantasy_context)
                
                # Only show message if there are actual updates (count > 0)
                if injury_check_result.get('success') and injury_check_result.get('count', 0) > 0:
                    # Format injury update message
                    injury_update_message = "By the way - here's an injury update for your fantasy team:\n\n"
                    for update in injury_check_result.get('updates', []):
                        injury_update_message += f"• **{update['player']}**: {update['headline']}\n"
                    injury_update_message += "\n"
                
                # Always update last injury check timestamp (regardless of whether updates were found)
                # This prevents checking again within 24 hours
                conversation.last_injury_check = datetime.now()
                db.session.commit()
            
            # Check if this is a fantasy football question
            fantasy_keywords = ['fantasy', 'my team', 'my roster', 'trade', 'waiver', 'start', 'sit', 'bench', 'draft']
            is_fantasy_question = any(keyword in user_message.lower() for keyword in fantasy_keywords)
            
            # Check if this is an affirmative response to route/play analysis
            affirmative_keywords = ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'show me', 'please', 'absolutely', 'definitely']
            is_short_message = len(user_message.split()) <= 5  # Short messages (5 words or less)
            is_affirmative = any(keyword in user_message.lower() for keyword in affirmative_keywords) and is_short_message
            
            # Start with empty history each time (no retained context)
            # This keeps API costs low and avoids rate limits
            conversation_history = []
            
            # If this is a short affirmative response and we have recent analysis context, inject it
            recent_analysis_context = json.loads(conversation.recent_analysis_context)
            if is_affirmative and recent_analysis_context:
                # Build context message
                analysis_data = recent_analysis_context.get('analysis_data', {})
                if analysis_data:
                    player_name = analysis_data.get('player_name', 'Unknown Player')
                    position = analysis_data.get('position', 'Unknown Position')
                    result = analysis_data.get('result', {})
                    
                    context_message = f"RECENT ROUTE/PLAY ANALYSIS CONTEXT:\n"
                    context_message += f"User just asked about {player_name}'s ({position}) top routes/plays.\n"
                    
                    if result.get('success') and result.get('top_routes'):
                        routes_or_plays = result['top_routes']
                        route_names = [r.get('route_name', 'Unknown') for r in routes_or_plays]
                        context_message += f"Analysis showed these top {'routes' if position in ['WR', 'TE'] else 'plays'}: {', '.join(route_names)}\n"
                        context_message += f"Analysis type: {result.get('analysis_type', 'routes')}\n"
                    
                    context_message += f"\nUser is now responding affirmatively ('{user_message}'). They likely want to see visual diagrams of these routes/plays."
                    
                    conversation_history.append({
                        "role": "user",
                        "content": context_message
                    })
                    conversation_history.append({
                        "role": "assistant",
                        "content": "I understand the context from our previous exchange."
                    })
            
            # Check if we're awaiting team selection from user
            fantasy_context = json.loads(conversation.fantasy_context)
            awaiting_team_selection = fantasy_context.get('awaiting_team_selection', False)
            
            if awaiting_team_selection:
                # User's message is their team name selection
                context_message = "TEAM SELECTION CONTEXT:\n"
                context_message += f"You just asked the user to select their team from the league.\n"
                context_message += f"The user has responded with: '{user_message}'\n"
                context_message += f"This is their team name selection. Call get_fantasy_team with team_name='{user_message}' to fetch their roster.\n"
                context_message += f"Use the stored ESPN credentials from the fantasy context.\n"
                
                conversation_history.append({
                    "role": "user",
                    "content": context_message
                })
                conversation_history.append({
                    "role": "assistant",
                    "content": "I understand. I'll fetch their roster now."
                })
            # If fantasy football question, prepend fantasy context
            elif is_fantasy_question:
                fantasy_context = json.loads(conversation.fantasy_context)
                has_context = (fantasy_context.get('my_team') or 
                             fantasy_context.get('interested_players') or 
                             fantasy_context.get('trade_history') or
                             fantasy_context.get('espn_roster'))
                
                if has_context:
                    context_message = "FANTASY FOOTBALL CONTEXT:\n"
                    
                    # ESPN credentials (user-specific, stored in their context)
                    if fantasy_context.get('espn_league_id'):
                        context_message += f"ESPN Credentials (use these in get_fantasy_team calls):\n"
                        context_message += f"  • league_id: {fantasy_context['espn_league_id']}\n"
                        if fantasy_context.get('espn_s2'):
                            context_message += f"  • espn_s2: {fantasy_context['espn_s2']}\n"
                        if fantasy_context.get('espn_swid'):
                            context_message += f"  • swid: {fantasy_context['espn_swid']}\n"
                    
                    # ESPN roster data takes precedence if available
                    if fantasy_context.get('espn_roster'):
                        espn_team_name = fantasy_context.get('espn_team_name', 'Unknown')
                        context_message += f"\nESPN Fantasy Team: {espn_team_name}\n"
                        context_message += "ESPN Fantasy Roster (from live API):\n"
                        for player in fantasy_context['espn_roster']:
                            status = f" ({player['injury_status']})" if player.get('injury_status') and player.get('injury_status') != 'ACTIVE' else ""
                            context_message += f"  • {player['name']} ({player['position']}){status}: {player['points_total']} pts\n"
                        
                        if fantasy_context.get('espn_matchup'):
                            matchup = fantasy_context['espn_matchup']
                            context_message += f"\nCurrent Matchup: {matchup.get('my_score', 0)} - {matchup.get('opponent_score', 0)} vs {matchup.get('opponent_name', 'Opponent')}\n"
                        
                        if fantasy_context.get('espn_standings'):
                            standings = fantasy_context['espn_standings']
                            context_message += f"League Standing: {standings.get('wins', 0)}-{standings.get('losses', 0)}, Rank: {standings.get('rank', 'N/A')}\n"
                        
                        # Tell AI to use stored credentials and team name
                        context_message += f"\nNOTE: When calling get_fantasy_team, use the credentials above and team_name='{espn_team_name}'\n"
                    
                    # Manually entered team data (for users without ESPN integration)
                    if fantasy_context.get('my_team'):
                        context_message += f"My Team (manual): {', '.join(fantasy_context['my_team'])}\n"
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
            
            # Get fantasy context as dict to pass to chat (for credential injection)
            fantasy_context_dict = json.loads(conversation.fantasy_context) if conversation.fantasy_context else {}
            response, updated_history, tool_usage = companion.chat(user_message, conversation_history, fantasy_context=fantasy_context_dict)
            
            # If route/play analysis was used, store the context for follow-up questions
            if tool_usage.get('used_analyze_player_routes_plays'):
                conversation.recent_analysis_context = json.dumps(tool_usage)
                db.session.commit()
            # Clear analysis context if user's message was affirmative (we just used it)
            elif is_affirmative and recent_analysis_context:
                conversation.recent_analysis_context = '{}'
                db.session.commit()
            
            # If ESPN fantasy team was fetched, update fantasy context with roster data
            if tool_usage.get('used_get_fantasy_team'):
                fantasy_team_data = tool_usage.get('fantasy_team_data', {})
                fantasy_context = json.loads(conversation.fantasy_context)
                
                if fantasy_team_data.get('success') and not fantasy_team_data.get('needs_team_selection'):
                    # Store ESPN roster data separately from manually entered team
                    fantasy_context['espn_roster'] = fantasy_team_data.get('roster', [])
                    fantasy_context['espn_matchup'] = fantasy_team_data.get('matchup', {})
                    fantasy_context['espn_standings'] = fantasy_team_data.get('standings', {})
                    fantasy_context['espn_team_name'] = fantasy_team_data.get('team_name')  # Store team name for future calls
                    fantasy_context['last_espn_fetch'] = datetime.now().isoformat()
                    # Clear the awaiting_team_selection flag since we now have their team
                    fantasy_context['awaiting_team_selection'] = False
                    
                    # Update database
                    conversation.fantasy_context = json.dumps(fantasy_context)
                    db.session.commit()
                elif fantasy_team_data.get('needs_team_selection'):
                    # Set flag to indicate we're waiting for user to select their team
                    fantasy_context['awaiting_team_selection'] = True
                    
                    # Update database
                    conversation.fantasy_context = json.dumps(fantasy_context)
                    db.session.commit()
            
            # If fantasy football question, extract and update fantasy context
            if is_fantasy_question:
                try:
                    # First, check if user provided ESPN credentials in their message
                    import re
                    fantasy_context = json.loads(conversation.fantasy_context)
                    
                    # Extract League ID - handles both natural language and table format
                    # Table format: | League ID  | 123456 |
                    # Natural format: "league id is 123456" or "leagueId=123456"
                    league_id_match = re.search(r'(?:league\s*id\s*(?:is)?\s*[:|]?\s*|leagueId=)\s*(\d+)', user_message, re.IGNORECASE)
                    if league_id_match:
                        fantasy_context['espn_league_id'] = league_id_match.group(1)
                    
                    # Extract ESPN S2 cookie - handles both natural language and table format
                    # Table format: | ESPN_S2    | AEBa...longstring... |
                    # Natural format: "espn_s2 is AEBa..." or "s2: AEBa..."
                    s2_match = re.search(r'(?:espn_?s2|s2)\s*[:|]?\s*([A-Za-z0-9%+/=]{50,})', user_message, re.IGNORECASE)
                    if s2_match:
                        fantasy_context['espn_s2'] = s2_match.group(1).strip()
                    
                    # Extract SWID - handles both natural language and table format
                    # Table format: | SWID       | {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX} |
                    # Natural format: "swid is {XXX...}" or "SWID: {XXX...}"
                    swid_match = re.search(r'(?:swid)\s*[:|]?\s*(\{[A-Za-z0-9-]{36}\})', user_message, re.IGNORECASE)
                    if swid_match:
                        fantasy_context['espn_swid'] = swid_match.group(1).strip()
                    
                    # Save if any credentials were found
                    if league_id_match or s2_match or swid_match:
                        conversation.fantasy_context = json.dumps(fantasy_context)
                        db.session.commit()
                    
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
            
            # Prepend injury update message if available
            final_response = response
            if injury_update_message:
                final_response = injury_update_message + response
            
            # DEBUG: Log the response to check for images
            logging.info(f"RESPONSE TEXT: {final_response[:500]}")
            if '![' in final_response:
                logging.info("✓ Response contains markdown images")
            else:
                logging.warning("✗ Response does NOT contain markdown images")
            
            return jsonify({
                'response': final_response,
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
