import json
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
from werkzeug.utils import secure_filename
from predict_face import predict_img
from send_email import send_email_to_parent
from send_sms import send_sms_to_parent

app = Flask(__name__)


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
    collection_profiles=db['profile_info']
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
        temp_details={
            'email': email,
            'full_name': full_name,
            'phone_number': phone_number
        }
        user_details = {
            'email': email,
            'full_name': full_name,
            'phone_number': phone_number
        }
        res=collection_profiles.insert_one(temp_details)
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
    gender=request.form.get('gender')
    height = request.form.get('height')

    weight = request.form.get('weight')
    description = request.form.get('description')
    moles = request.form.get('moles')
    last_seen_time = request.form.get('last_seen_time')
    last_seen_location = request.form.get('last_seen_location')
    clothing_description = request.form.get('clothing_description')
    physical_features = request.form.get('physical_features')
    behavioral_characteristics = request.form.get('behavioral_characteristics')
    medical_information = request.form.get('medical_information')
    contact_information = request.form.get('alternate_mobile')
    # known_locations = request.form.get('known_locations')
    images = request.files.getlist('images')
    res_uid1=collection1.find_one({"token":token})
    uid=res_uid1["uid"]
    # email=res_uid1["email"]

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
        'weight':weight,
        'description': description,
        'moles': moles,
        'last_seen_time': last_seen_time,
        'last_seen_location': last_seen_location,
        'clothing_description': clothing_description,
        'physical_features': physical_features,
        'behavioral_characteristics': behavioral_characteristics,
        'medical_information': medical_information,
        'alternate_mobile': contact_information,
        'email':email,
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

@app.route('/update_profile', methods=['POST'])
def update_profile():
    collection1=db["login_info"]
    collection_profiles=db['profile_info']
    token = request.form.get('token')
    pincode=request.form.get('pincode')
    email = request.form.get('email')# Assuming you store the email in the session during login
    phone_number = request.form.get('phone_number')
    # Retrieve form data including additional fields
    full_name = request.form.get('full_name')
    date_of_birth = request.form.get('date_of_birth')
    address = request.form.get('address')
    photo = request.files.get('photo')
    gender = request.form.get('gender')
    occupation = request.form.get('occupation')
    # interests = request.form.get('interests')
    emergency_contact = request.form.get('emergency_contact')
    res_uid1=collection1.find_one({"token":token})
    uid=res_uid1["uid"]
    # Get the existing profile data
    existing_profile = collection_profiles.find_one({'email': email})

    # Update only the fields provided in the request
    updated_fields = {}
    if full_name:
        updated_fields['full_name'] = full_name
    if date_of_birth:
        updated_fields['date_of_birth'] = date_of_birth
    if address:
        updated_fields['address'] = address
    if photo:
        updated_fields['photo'] = save_photo(photo, uid)
    if gender:
        updated_fields['gender'] = gender
    if occupation:
        updated_fields['occupation'] = occupation
    if pincode:
        updated_fields['pincode'] = pincode
    if emergency_contact:
        updated_fields['emergency_contact'] = emergency_contact

    # Update the profile data
    result = collection_profiles.update_one({'email': email}, {'$set': updated_fields})

    if result.modified_count > 0:
        return jsonify({'message': 'Profile updated successfully.'}), 200
    else:
        return jsonify({'message': 'No changes to update.'}), 200

@app.route('/get_user_profiles', methods=['GET'])
def get_user_profiles():
    collection_profiles=db['children_info']
    matched_profiles=db['matching_info']
    # Parse query parameters for search and filtering
    search_query = request.args.get('search_query')
    gender = request.args.get('gender')
    min_age = request.args.get('min_age')
    max_age = request.args.get('max_age')
    min_last_seen_time = request.args.get('min_last_seen_time')
    max_last_seen_time = request.args.get('max_last_seen_time')
    is_matched = request.args.get('is_matched')
    sort_field=request.args.get('sort_field')
    sort_order=request.args.get('sort_order')
    # occupation = request.args.get('occupation')
    # Add more filter parameters as needed

    # Construct the query based on filters
    query = {}
    if search_query:
        query['$or'] = [
            {'name': {'$regex': f'.*{search_query}.*', '$options': 'i'}},
            {'last_seen_location': {'$regex': f'.*{search_query}.*', '$options': 'i'}}
        ]   
    if gender:
        query['gender'] = gender
    if min_age or max_age:
        query['age'] = {}  # Create a nested dictionary for date of birth range query
        if min_age:
            query['age']['$gte'] = min_age
        if max_age:
            query['age']['$lte'] = max_age
    if min_last_seen_time or max_last_seen_time:
        query['last_seen_time'] = {}  # Create a nested dictionary for last seen time range query
        if min_last_seen_time:
            query['last_seen_time']['$gte'] = datetime.strptime(min_last_seen_time, '%Y-%m-%d')
        if max_last_seen_time:
            query['last_seen_time']['$lte'] = datetime.strptime(max_last_seen_time, '%Y-%m-%d')
    if is_matched is not None:
        query['is_matched'] = bool(is_matched)
        # query['$or'] = [{'full_name': {'$regex': search_query, '$options': 'i'}}, {'address': {'$regex': search_query, '$options': 'i'}}]
    # if gender:
    #     query['gender'] = gender
    # if occupation:
    #     query['occupation'] = occupation
        
    user_reports= list(collection_profiles.find(query).sort("age", 1 if sort_order == 'asc' else -1))
    matched_profiles=list(matched_profiles.find({"matched":True}))
    print(user_reports,matched_profiles)
    for i in user_reports:
        i['_id'] = str(i['_id'])
        i['last_seen_time']=str(i['last_seen_time'])
        i["matched"]=False
        for j in matched_profiles:
            if i["images"]==j["child_id"]:
                i["matched"]=True
                i['helper_profile_email']=j['helper_profile']["email"]
                i['helper_full_name']=j['helper_full_name']
                i['helper_phone']=j['helper_phone']
                break
        
    return jsonify({'reports': list(user_reports)}), 200
    
@app.route('/predict', methods=['POST'])
def predict():
    collection=db["matching_info"]
    child_profile=db["children_info"]
    collection2=db["profile_info"]
    collection1=db["login_info"]
    token=request.form.get("token")
    lat=request.form.get("lat")
    lon=request.form.get("lon")
    image=request.files["photo"]
    temp_session={
            'token':token
        }
    existing_session = collection1.find_one(temp_session)
    uid=existing_session["uid"]
    
    image_loc=save_photo_matching(image,uid)
    email=existing_session["username"]
    helper_profile=collection2.find_one({'email':email})
    helper_phone=helper_profile["phone_number"]
    helper_full_name=helper_profile["full_name"]
    x=predict_img(image_loc)
    c=x.split("_")
    temp_child={
        'images':x
    }

    child_name=c[1]
    
    res=child_profile.find_one(temp_child)
    child_age=res["age"]
    child_description=res["description"]
    # email=res["email"]
    # parent_profile=db["profile_info"]
    mobile=res["alternate_mobile"]

    # res=profile.find_one({"child_name":child_name})
    
    # print(token,session)
    # Verify login before allowing logout
    # if existing_session:
    #     collection.delete_one(temp_session)
    if x!="No image Found":
        res={
        'image':image_loc,
        'email':email,
        'helper_profile':helper_profile,
        'helper_full_name':helper_full_name,
        'helper_phone':helper_phone,
        'child_id':x,
        'matched':True,
        'location':[lat,lon],
        
        }
        try:
            collection.insert_one(res)
        except:
            pass
        send_email_to_parent(email,child_name,child_age,child_description,lat,lon,helper_full_name,helper_phone)
        #send_sms_to_parent(child_name,child_age,lat,lon,helper_full_name,helper_phone,mobile)
        
        return jsonify({'message': 'Face Recognition done',"name":child_name,'age':child_age,'child_description':child_description,'parent_mobile':mobile}), 200
    else:
        res={
        'image':image_loc,
        'email':email,
        'helper_profile':helper_profile,
        'helper_full_name':helper_full_name,
        'helper_phone':helper_phone,
        'child_id':"Not Found",
        'matched':False
    }
        # send_email_to_parent(email,child_name,child_age,child_description,lat,lon,helper_full_name,helper_phone)
        return jsonify({"message":"No Face matched with the records"}),500
    # else:
    #     return jsonify({'error': 'You are not logged in.'}), 401
def save_photo_matching(photo, uid):
    if photo:
        x=os.getcwd()
        filename = secure_filename(photo.filename)
        dest_directory=os.path.join(x,"history",uid)
        os.makedirs(dest_directory, exist_ok=True)
        count=str(len(list(os.scandir(dest_directory))))
        file_loc=os.path.join(dest_directory, count+".jpg")
        photo.save(file_loc)
        return file_loc
def save_photo(photo, uid):
    if photo:
        x=os.getcwd()
        filename = secure_filename(photo.filename)
        dest_directory=os.path.join(x,"profile")
        os.makedirs(dest_directory, exist_ok=True)
        file_loc=os.path.join(dest_directory, uid+".jpg")
        photo.save(os.path.join(dest_directory, uid+".jpg"))
        return file_loc
    else:
        return None
#
def save_images(images,uid,name):
    x=os.getcwd()
    count=0
    # cloudinary.uploader.upload("https://upload.wikimedia.org/wikipedia/commons/a/ae/Olympic_flag.jpg", 
    # public_id = "test/olympic_flag")
    # print("hi")
    for file in images:
        count+=1
        destination_directory=os.path.join(x, "training", uid + "_" + name)
        os.makedirs(destination_directory, exist_ok=True)
        print(str(count)+".png") 
        cloudinary.uploader.upload(file,public_id = "training/"+uid+"_"+name+"/"+str(count)+".png")
        file.seek(0)
        file.save(os.path.join(destination_directory, str(count) + ".jpg"))
    return uid+"_"+name


if __name__ == '__main__':
    app.run(debug=True)
