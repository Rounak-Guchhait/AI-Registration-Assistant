"""
AI Registration Assistant - Flask Web App
Free Online AI & Data Science Internship Task AI-SS-001

Serves a webpage with a floating chat bubble widget (like Amazon),
and exposes a /chat API endpoint that reuses the RegistrationAssistant
chatbot logic. Each browser session keeps its own conversation state.
"""

import os
import sys

from flask import Flask, jsonify, render_template, request, session

# Ensure the project directory is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chatbot import RegistrationAssistant
from admin import admin_bp
from seed import seed_database

app = Flask(__name__)
app.secret_key = 'ai-registration-assistant-secret-key-for-sessions'

# Register the admin dashboard routes (served under /admin)
app.register_blueprint(admin_bp)

# Auto-seed the database with 100 sample records if empty.
if seed_database(100):
    print('  [seed] Inserted 100 sample registrations into the database.')
else:
    print('  [seed] Database already has records — seed skipped.')

# Each browser session keeps its own chatbot instance so that
# multiple users can register independently at the same time.
assistants = {}


def get_assistant():
    """Return the unique chatbot instance for the current session."""
    sid = session.get('sid')
    if sid is None:
        sid = os.urandom(16).hex()
        session['sid'] = sid
    if sid not in assistants:
        assistants[sid] = RegistrationAssistant()
    return assistants[sid], sid


@app.route('/')
def index():
    """Serve the main page with the chat widget."""
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    """Receive a user message and return the assistant's reply."""
    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()

    if not message:
        return jsonify({'reply': 'Please type a message.', 'reset': False})

    assistant, sid = get_assistant()

    # Handle explicit reset request (e.g., "new registration")
    if message.lower() in ('/reset', 'restart'):
        assistant.reset_conversation()
        assistants[sid] = RegistrationAssistant()
        return jsonify({
            'reply': 'Okay, let\'s start a fresh registration. What is your full name?',
            'reset': True
        })

    reply = assistant.handle_message(message)
    return jsonify({'reply': reply, 'reset': False})


if __name__ == '__main__':
    # Bind to 0.0.0.0 and use the PORT provided by the host (e.g. Render).
    # Locally this defaults to 5000 on http://127.0.0.1:5000
    port = int(os.environ.get('PORT', 5000))
    print('\n' + '=' * 60)
    print('  AI REGISTRATION ASSISTANT - WEB')
    print(f'  Open your browser at:  http://127.0.0.1:{port}')
    print('  Press Ctrl+C to stop.')
    print('=' * 60)
    app.run(host='0.0.0.0', port=port, debug=False)
