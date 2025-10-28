#!/usr/bin/env python3
"""
NFL AI Companion - Command Line Demo
Run this to interact with your NFL companion without the web interface
"""

import os
import sys

# Import the NFLCompanion class from app.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import NFLCompanion

def main():
    print("=" * 60)
    print("🏈 NFL AI COMPANION - CLI Demo")
    print("=" * 60)

    # Initialize the companion
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("\n⚠️  ERROR: ANTHROPIC_API_KEY not set!")
        print("Please set it with: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    companion = NFLCompanion(api_key)
    conversation_history = []

    print("\n🏈 Welcome! I'm your NFL AI companion.")
    print("\nI can help you with:")
    print("  • Live scores and game updates")
    print("  • Tactical analysis and X's & O's")
    print("  • Fantasy football decisions")
    print("  • Deep dives into strategy and matchups")
    print("\nType 'quit' or 'exit' to end the conversation.")
    print("=" * 60)

    while True:
        try:
            # Get user input
            print("\n" + "You: ", end="")
            user_message = input().strip()

            if not user_message:
                continue

            if user_message.lower() in ['quit', 'exit', 'q']:
                print("\n🏈 Thanks for chatting! See you next game day!")
                break

            # Get response
            print("\n🏈 NFL Companion: ", end="", flush=True)
            response, conversation_history = companion.chat(user_message, conversation_history)
            print(response)
            print("\n" + "-" * 60)

        except KeyboardInterrupt:
            print("\n\n🏈 Thanks for chatting! See you next game day!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Try asking something else!")

if __name__ == '__main__':
    main()
