from flask import Flask, jsonify, request,session
import requests
import os
from dotenv import load_dotenv
import jwt 
import pyrebase
# from flask_session import Session
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from os import walk
import cloudinary,cloudinary.uploader

app = Flask(__name__)

app.config.update(
    SESSION_COOKIE_SECURE=True,  # Enable secure session cookie (for HTTPS)
    SESSION_COOKIE_SAMESITE='None'  # Allow cross-site usage (for HTTPS)
)

# app.config['SESSION_TYPE'] = 'filesystem'  # Change session storage to filesystem


# Load environment variables
load_dotenv()

app.secret_key = os.getenv('Secret_Key')  # Replace this with your secret key
CORS(app,supports_credentials=True)
firebase_api_key = os.getenv('FIREBASE_API_KEY')
firebase_auth_domain = os.getenv('FIREBASE_AUTH_DOMAIN')
firebase_project_id = os.getenv('FIREBASE_PROJECT_ID')
mongo_client = MongoClient('mongodb+srv://bhovan:bhovan123@cluster0.dob8icq.mongodb.net/')  # Replace with your MongoDB connection string
db = mongo_client['Missing_child']

#cloudinary

          
cloudinary.config( 
  cloud_name = "dognhm5vd", 
  api_key = "957236922523751", 
  api_secret = "W5bweTgdJxh1aEtKvEiVEo5_hIo" 
)
# firebase_config = {
#     'apiKey': firebase_api_key,
#     'authDomain': firebase_auth_domain,
#     'projectId': firebase_project_id
# }
firebase_config={
  'apiKey': "AIzaSyDqeKADnaDw3WY3e4asTUBcuLUviU24Fow",
  'authDomain': "child-missing-1.firebaseapp.com",
  'databaseURL': "https://child-missing-1-default-rtdb.firebaseio.com",
  'projectId': "child-missing-1",
  'storageBucket': "child-missing-1.appspot.com",
  'messagingSenderId': "427714578606",
  'appId': "1:427714578606:web:77ba406393730feac5453f",
  'measurementId': "G-18YTPER52K"
}
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    phone_number = request.form.get('phone')

    if not email or not password or not full_name or not phone_number:
        print(not email,not password,not full_name,not phone_number)
        return jsonify({'error': 'All fields are required.'}), 401

    # Firebase sign-up endpoint
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={firebase_api_key}"
    payload = {
        'email': email,
        'password': password,
        'returnSecureToken': True
    }
    response = requests.post(url, json=payload)

    if response.ok:
        # Store additional user details in a database or any other storage mechanism
        # For this example, just return the details
        user_details = {
            'email': email,
            'full_name': full_name,
            'phone_number': phone_number
        }
        return jsonify({'message': 'Registration successful.', 'user_details': user_details}), 200
    else:
        return jsonify({'error': 'Registration failed.'}), 400
    
@app.route('/login', methods=['POST'])
def login():
    collection = db['login_info']
    email = request.form.get('email')
    password = request.form.get('password')
    print(email,password)
    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    # Firebase sign-in endpoint
    # url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={firebase_api_key}"
    # payload = {
    #     'email': email,
    #     'password': password,
    #     'returnSecureToken': True
    # }
    # response = requests.post(url, json=payload)
    temp_session={
            'username':email
        }
    existing_session = collection.find_one(temp_session)
    if existing_session:
        return jsonify({'message': 'Already Loggedin successful.','token':existing_session['token']}), 200
    user=auth.sign_in_with_email_and_password(email,password)
    print(user)


    if user:
        payload = {'username': email,'uid':user['localId']}  # Customize payload as needed
        token = jwt.encode(payload, app.secret_key, algorithm='HS256')
        # Set session after successful login
        # session[token] = payload
        temp_session={
            'username':email,
            'uid':user['localId'],
            'token':token
        }
        result = collection.insert_one(temp_session)
        return jsonify({'message': 'Login successful.','token':token}), 200
    else:
        return jsonify({'error': 'Login failed.'}), 400
    
@app.route('/reset_password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')

    if not email:
        return jsonify({'error': 'Email is required.'}), 400

    # Firebase password reset endpoint
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={firebase_api_key}"
    payload = {
        'email': email,
        'requestType': 'PASSWORD_RESET'
    }
    response = requests.post(url, json=payload)

    if response.ok:
        return jsonify({'message': 'Password reset email sent successfully.'}), 200
    else:
        error_message = response.json().get('error', {}).get('message', 'Password reset failed.')
        return jsonify({'error': error_message}), 400

@app.route('/logout', methods=['POST'])
def logout():
    collection=db["login_info"]
    token=request.form.get("token")
    
    temp_session={
            'token':token
        }
    existing_session = collection.find_one(temp_session)

   
    print(token,session)
    # Verify login before allowing logout
    if existing_session:
        collection.delete_one(temp_session)
        return jsonify({'message': 'Logged out successfully.'}), 200
    else:
        return jsonify({'error': 'You are not logged in.'}), 401

@app.route("/session",methods=["GET"])
def get_sessions():
    print(session)
    return jsonify({"session":session}),200


@app.route('/report-missing-child', methods=['POST'])
def report_missing_child():
    collection = db['children_info']
    collection1=db['login_info']
    # Retrieve form data including additional fields
    token=request.form.get('token')
    name = request.form.get('name')
    age = request.form.get('age')
    height = request.form.get('height')
    description = request.form.get('description')
    moles = request.form.get('moles')
    last_seen_time = request.form.get('last_seen_time')
    last_seen_location = request.form.get('last_seen_location')
    clothing_description = request.form.get('clothing_description')
    physical_features = request.form.get('physical_features')
    behavioral_characteristics = request.form.get('behavioral_characteristics')
    medical_information = request.form.get('medical_information')
    contact_information = request.form.get('contact_information')
    known_locations = request.form.get('known_locations')
    images = request.files.getlist('images')
    uid1=collection1.find_one({"token":token})
    uid=uid1["uid"]

    if not name or not age or not height or not description or not last_seen_time or not last_seen_location:
        return jsonify({'error': 'Name, age, height, description, last_seen_time, and last_seen_location are required.'}), 400

    # Convert last_seen_time to datetime object (assuming the format is YYYY-MM-DD HH:MM:SS)
    try:
        last_seen_time = datetime.strptime(last_seen_time, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({'error': 'Invalid last_seen_time format. Use YYYY-MM-DD HH:MM:SS.'}), 400
    
    # Save images to EC2 system
    uploaded_files = save_images(images,uid,name)

    # Save data to MongoDB including additional fields
    child_data = {
        'uid':uid,
        'name': name,
        'age': age,
        'height': height,
        'description': description,
        'moles': moles,
        'last_seen_time': last_seen_time,
        'last_seen_location': last_seen_location,
        'clothing_description': clothing_description,
        'physical_features': physical_features,
        'behavioral_characteristics': behavioral_characteristics,
        'medical_information': medical_information,
        'contact_information': contact_information,
        'known_locations': known_locations,
        'images': uploaded_files
    }
    try:
        result = collection.insert_one(child_data)
    except:
        return jsonify({'error':'Already existing data'}),500

    if result.inserted_id:
        return jsonify({'message': 'Missing child report created successfully.'}), 200
    else:
        return jsonify({'error': 'Failed to create missing child report.'}), 500

#
def save_images(images,uid,name):
    x=os.getcwd()
    count=0
    # cloudinary.uploader.upload("https://upload.wikimedia.org/wikipedia/commons/a/ae/Olympic_flag.jpg", 
    # public_id = "test/olympic_flag")
    print("hi")
    for file in images:
        count+=1
        destination_directory=os.path.join(x, "training", uid + "_" + name)
        os.makedirs(destination_directory, exist_ok=True)
        print(str(count)+".png") 
        # file.save(x+"\\training\\"+uid+"_"+name+"\\"+str(count)+".png")
        cloudinary.uploader.upload(file,public_id = "training/"+uid+"_"+name+"/"+str(count)+".png")
        file.save(os.path.join(destination_directory, str(count) + ".png"))
    return uid+"_"+name

if __name__ == '__main__':
    app.run(debug=True)
