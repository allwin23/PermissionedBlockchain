from fabric_interface.wallet import wallet
from functools import wraps
from flask import Blueprint, request, jsonify, session
import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'


auth_bp = Blueprint('auth', __name__)

# Basic hardcoded validation for demonstration
USERS = {
    "alice": "password123",
    "admin": "admin"
}


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Unauthorized', 'message': 'Please log in first'}), 401

        # Verify identity exists in wallet
        identity = wallet.load_identity(session['username'])
        if not identity:
            return jsonify({'error': 'Unauthorized', 'message': 'Wallet identity missing'}), 401

        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Bad Request', 'message': 'Missing credentials'}), 400

    username = data['username']
    password = data['password']

    if username in USERS and USERS[username] == password:
        # Load identity
        identity = wallet.load_identity(username)
        if identity:
            session['username'] = username
            return jsonify({'message': 'Logged in successfully'}), 200
        else:
            return jsonify({'error': 'Internal Error', 'message': 'Identity not found in wallet directory'}), 500
    else:
        return jsonify({'error': 'Unauthorized', 'message': 'Invalid credentials'}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    return jsonify({'username': session['username']}), 200
