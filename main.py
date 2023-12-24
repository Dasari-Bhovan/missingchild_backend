from flask import Flask, jsonify, request, session
import requests
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()

app.secret_key = os.getenv('Secret_Key')  # Replace this with your secret key

firebase_api_key = os.getenv('FIREBASE_API_KEY')
firebase_auth_domain = os.getenv('FIREBASE_AUTH_DOMAIN')
firebase_project_id = os.getenv('FIREBASE_PROJECT_ID')

firebase_config = {
    'apiKey': firebase_api_key,
    'authDomain': firebase_auth_domain,
    'projectId': firebase_project_id
}

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    # Firebase sign-up endpoint
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={firebase_api_key}"
    payload = {
        'email': email,
        'password': password,
        'returnSecureToken': True
    }
    response = requests.post(url, json=payload)

    if response.ok:
        return jsonify({'message': 'Registration successful.'}), 200
    else:
        return jsonify({'error': 'Registration failed.'}), 400

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    # Firebase sign-in endpoint
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={firebase_api_key}"
    payload = {
        'email': email,
        'password': password,
        'returnSecureToken': True
    }
    response = requests.post(url, json=payload)

    if response.ok:
        # Set session after successful login
        session['email'] = email
        return jsonify({'message': 'Login successful.'}), 200
    else:
        return jsonify({'error': 'Login failed.'}), 400


@app.route('/logout', methods=['POST'])
def logout():
    # Verify login before allowing logout
    if 'email' in session:
        session.pop('email', None)
        return jsonify({'message': 'Logged out successfully.'}), 200
    else:
        return jsonify({'error': 'You are not logged in.'}), 401


@app.route('/pre-login-verify', methods=['GET'])
def pre_login_verify():
    # Check if user is already logged in
    if 'email' in session:
        return jsonify({'message': 'User already logged in.', 'email': session['email']}), 200
    else:
        return jsonify({'message': 'User not logged in.'}), 401


if __name__ == '__main__':
    app.run(debug=True)
