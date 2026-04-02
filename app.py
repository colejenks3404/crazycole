from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import time

app = Flask(__name__)
CORS(app)

COMMENTS_FILE = 'comments.json'
POLL_FILE = 'poll.json'

# In-memory user storage (for demo purposes)
users = {}

def load_comments():
    if not os.path.exists(COMMENTS_FILE):
        return []
    try:
        with open(COMMENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_comments(comments):
    with open(COMMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)

def load_poll():
    # default poll data
    default = {
        'id': 'next_featured_pet',
        'question': 'Vote for the next featured pet',
        'options': [
            {'id': 'harriet', 'label': 'Harriet', 'votes': 0},
            {'id': 'max', 'label': 'Max', 'votes': 0},
            {'id': 'luna', 'label': 'Luna', 'votes': 0}
        ]
    }
    if not os.path.exists(POLL_FILE):
        save_poll(default)
        return default
    try:
        with open(POLL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default

def save_poll(poll):
    with open(POLL_FILE, 'w', encoding='utf-8') as f:
        json.dump(poll, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if username in users and users[username] == password:
        return jsonify({'success': True, 'message': 'Login successful'})
    return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if username in users:
        return jsonify({'success': False, 'message': 'Username already exists'})
    users[username] = password
    return jsonify({'success': True, 'message': 'Account created successfully'})

@app.route('/api/comments', methods=['GET'])
def get_comments():
    comments = load_comments()
    # Return comments ordered newest-first
    comments_sorted = sorted(comments, key=lambda c: c.get('ts', 0), reverse=True)
    return jsonify(comments_sorted)

@app.route('/api/comments', methods=['POST'])
def post_comment():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid payload'}), 400

    comments = load_comments()
    new_comment = {
        'id': data.get('id') or str(int(time.time() * 1000)),
        'username': data.get('username') or 'Anonymous',
        'text': data.get('text') or '',
        'parentId': data.get('parentId'),
        'likes': int(data.get('likes') or 0),
        'ts': int(time.time())
    }
    comments.insert(0, new_comment)
    save_comments(comments)
    return jsonify(new_comment), 201

@app.route('/api/comments/<comment_id>/like', methods=['POST'])
def like_comment(comment_id):
    comments = load_comments()
    for c in comments:
        if c.get('id') == comment_id:
            c['likes'] = int(c.get('likes', 0)) + 1
            save_comments(comments)
            return jsonify({'success': True, 'likes': c['likes']})
    return jsonify({'success': False, 'message': 'Not found'}), 404


@app.route('/api/poll', methods=['GET'])
def get_poll():
    poll = load_poll()
    return jsonify(poll)


@app.route('/api/poll/vote', methods=['POST'])
def vote_poll():
    data = request.get_json()
    if not data or 'option' not in data:
        return jsonify({'success': False, 'message': 'Invalid payload'}), 400
    option_id = data.get('option')
    poll = load_poll()
    found = False
    for opt in poll.get('options', []):
        if opt.get('id') == option_id:
            opt['votes'] = int(opt.get('votes', 0)) + 1
            found = True
            break
    if not found:
        return jsonify({'success': False, 'message': 'Option not found'}), 404
    save_poll(poll)
    return jsonify({'success': True, 'poll': poll})

if __name__ == '__main__':
    app.run(debug=True)