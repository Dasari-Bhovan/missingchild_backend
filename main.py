import json
from flask import Flask, jsonify, request, session
import requests
import os
from dotenv import load_dotenv
import jwt
import pyrebase
import base64

# from flask_session import Session
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from os import walk
import cloudinary, cloudinary.uploader
from werkzeug.utils import secure_filename
from predict_face import predict_img
from send_email import send_email_to_parent
from send_sms import send_sms_to_parent

app = Flask(__name__)


# app.config['SESSION_TYPE'] = 'filesystem'  # Change session storage to filesystem


# Load environment variables
load_dotenv()

app.secret_key = os.getenv("Secret_key")  # Replace this with your secret key
CORS(app, supports_credentials=True)
firebase_api_key = os.getenv("FIREBASE_API_KEY")
firebase_auth_domain = os.getenv("FIREBASE_AUTH_DOMAIN")
firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
mongo_client = MongoClient(
    "mongodb+srv://bhovan:bhovan123@cluster0.dob8icq.mongodb.net/"
)  # Replace with your MongoDB connection string
db = mongo_client["Missing_child"]

# cloudinary


cloudinary.config(
    cloud_name="dognhm5vd",
    api_key="957236922523751",
    api_secret="W5bweTgdJxh1aEtKvEiVEo5_hIo",
)
# firebase_config = {
#     'apiKey': firebase_api_key,
#     'authDomain': firebase_auth_domain,
#     'projectId': firebase_project_id
# }
firebase_config = {
    "apiKey": "AIzaSyDqeKADnaDw3WY3e4asTUBcuLUviU24Fow",
    "authDomain": "child-missing-1.firebaseapp.com",
    "databaseURL": "https://child-missing-1-default-rtdb.firebaseio.com",
    "projectId": "child-missing-1",
    "storageBucket": "child-missing-1.appspot.com",
    "messagingSenderId": "427714578606",
    "appId": "1:427714578606:web:77ba406393730feac5453f",
    "measurementId": "G-18YTPER52K",
}
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()


@app.route("/register", methods=["POST"])
def register():
    collection_profiles = db["profile_info"]
    email = request.form.get("email")
    password = request.form.get("password")
    full_name = request.form.get("full_name")
    phone_number = request.form.get("phone")

    if not email or not password or not full_name or not phone_number:
        print(not email, not password, not full_name, not phone_number)
        return jsonify({"error": "All fields are required."}), 401

    # Firebase sign-up endpoint
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={firebase_api_key}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=payload)
    print(response)
    if response.ok:
        # Store additional user details in a database or any other storage mechanism
        # For this example, just return the details
        temp_details = {
            "email": email,
            "full_name": full_name,
            "phone_number": phone_number,
        }
        user_details = {
            "email": email,
            "full_name": full_name,
            "phone_number": phone_number,
        }
        res = collection_profiles.insert_one(temp_details)
        return (
            jsonify(
                {"message": "Registration successful.", "user_details": user_details}
            ),
            200,
        )
    else:
        return jsonify({"error": "Registration failed."}), 400


@app.route("/login", methods=["POST"])
def login():
    collection = db["login_info"]
    email = request.form.get("email")
    password = request.form.get("password")
    print(email, password)
    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    # Firebase sign-in endpoint
    # url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={firebase_api_key}"
    # payload = {
    #     'email': email,
    #     'password': password,
    #     'returnSecureToken': True
    # }
    # response = requests.post(url, json=payload)
    temp_session = {"username": email}
    existing_session = collection.find_one(temp_session)
    if existing_session:
        return (
            jsonify(
                {
                    "message": "Already Loggedin successful.",
                    "token": existing_session["token"],
                }
            ),
            200,
        )
    user = auth.sign_in_with_email_and_password(email, password)
    print(user)

    if user:
        payload = {
            "username": email,
            "uid": user["localId"],
        }  # Customize payload as needed
        token = jwt.encode(payload, app.secret_key, algorithm="HS256")
        # Set session after successful login
        # session[token] = payload
        temp_session = {"username": email, "uid": user["localId"], "token": token}
        result = collection.insert_one(temp_session)
        return jsonify({"message": "Login successful.", "token": token}), 200
    else:
        return jsonify({"error": "Login failed."}), 400


@app.route("/reset_password", methods=["POST"])
def forgot_password():
    email = request.form.get("email")

    if not email:
        return jsonify({"error": "Email is required."}), 400

    # Firebase password reset endpoint
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={firebase_api_key}"
    payload = {"email": email, "requestType": "PASSWORD_RESET"}
    response = requests.post(url, json=payload)

    if response.ok:
        return jsonify({"message": "Password reset email sent successfully."}), 200
    else:
        error_message = (
            response.json().get("error", {}).get("message", "Password reset failed.")
        )
        return jsonify({"error": error_message}), 400


@app.route("/logout", methods=["POST"])
def logout():
    collection = db["login_info"]
    token = request.form.get("token")

    temp_session = {"token": token}
    existing_session = collection.find_one(temp_session)

    print(token, session)
    # Verify login before allowing logout
    if existing_session:
        collection.delete_one(temp_session)
        return jsonify({"message": "Logged out successfully."}), 200
    else:
        return jsonify({"error": "You are not logged in."}), 401


@app.route("/session", methods=["GET"])
def get_sessions():
    print(session)
    return jsonify({"session": session}), 200


@app.route("/report-missing-child", methods=["POST"])
def report_missing_child():
    collection = db["children_info"]
    collection1 = db["login_info"]
    # Retrieve form data including additional fields
    token = request.form.get("token")
    name = request.form.get("name")
    age = request.form.get("age")
    gender = request.form.get("gender")
    height = request.form.get("height")

    weight = request.form.get("weight")
    description = request.form.get("description")
    moles = request.form.get("moles")
    last_seen_time = request.form.get("last_seen_time")
    last_seen_location = request.form.get("last_seen_location")
    clothing_description = request.form.get("clothing_description")
    physical_features = request.form.get("physical_features")
    behavioral_characteristics = request.form.get("behavioral_characteristics")
    medical_information = request.form.get("medical_information")
    contact_information = request.form.get("alternate_mobile")
    # known_locations = request.form.get('known_locations')
    images = request.files.getlist("images")
    res_uid1 = collection1.find_one({"token": token})
    uid = res_uid1["uid"]
    email = res_uid1["username"]

    if (
        not name
        or not age
        or not height
        or not description
        or not last_seen_time
        or not last_seen_location
    ):
        return (
            jsonify(
                {
                    "error": "Name, age, height, description, last_seen_time, and last_seen_location are required."
                }
            ),
            400,
        )

    # Convert last_seen_time to datetime object (assuming the format is YYYY-MM-DD HH:MM:SS)
    try:
        last_seen_time = datetime.strptime(last_seen_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return (
            jsonify(
                {"error": "Invalid last_seen_time format. Use YYYY-MM-DD HH:MM:SS."}
            ),
            400,
        )

    # Save images to EC2 system
    uploaded_files = save_images(images, uid, name)

    # Save data to MongoDB including additional fields
    child_data = {
        "uid": uid,
        "name": name,
        "age": age,
        "height": height,
        "weight": weight,
        "description": description,
        "moles": moles,
        "last_seen_time": last_seen_time,
        "last_seen_location": last_seen_location,
        "clothing_description": clothing_description,
        "physical_features": physical_features,
        "behavioral_characteristics": behavioral_characteristics,
        "medical_information": medical_information,
        "alternate_mobile": contact_information,
        "email": email,
        "images": uploaded_files,
    }

    try:
        result = collection.insert_one(child_data)
    except:
        return jsonify({"error": "Already existing data"}), 500

    if result.inserted_id:
        return jsonify({"message": "Missing child report created successfully."}), 200
    else:
        return jsonify({"error": "Failed to create missing child report."}), 500


@app.route("/update_profile", methods=["GET"])
def update_profile():
    collection1 = db["login_info"]
    collection_profiles = db["profile_info"]
    token = request.args.get("token")
    pincode = request.args.get("pincode")
    # email = request.args.get('email')# Assuming you store the email in the session during login
    phone_number = request.args.get("phone_number")
    age = request.args.get("age")
    gender = request.args.get("gender")
    height = request.args.get("height")
    weight = request.args.get("weight")
    # Retrieve form data including additional fields
    full_name = request.args.get("full_name")
    # date_of_birth = request.form.get('date_of_birth')
    address = request.args.get("address")
    occupation = request.args.get("occupation")
    # interests = request.form.get('interests')
    # emergency_contact = request.form.get('emergency_contact')
    res_uid1 = collection1.find_one({"token": token})
    uid = res_uid1["uid"]
    email = res_uid1["username"]
    # Get the existing profile data
    existing_profile = collection_profiles.find_one({"email": email})

    # Update only the fields provided in the request
    updated_fields = {}
    if full_name:
        updated_fields["full_name"] = full_name
    if age:
        updated_fields["age"] = age
    if address:
        updated_fields["address"] = address
    if gender:
        updated_fields["gender"] = gender
    if occupation:
        updated_fields["occupation"] = occupation
    if pincode:
        updated_fields["pincode"] = pincode
    if phone_number:
        updated_fields["phone_number"] = phone_number
    if height:
        updated_fields["height"] = height
    if weight:
        updated_fields["weight"] = weight

    # Update the profile data
    result = collection_profiles.update_one({"email": email}, {"$set": updated_fields})

    if result.modified_count > 0:
        return jsonify({"message": "Profile updated successfully."}), 200
    else:
        return jsonify({"message": "No changes to update."}), 200


@app.route("/profile", methods=["PUT"])
def get_profile():
    # Retrieve email from request headers or wherever it's stored
    collection1 = db["login_info"]
    collection = db["profile_info"]

    token = request.form.get("token")
    res_uid1 = collection1.find_one({"token": token})

    uid = res_uid1["uid"]
    email = res_uid1["username"]
    print(email)
    user_profiles = collection.find_one({"email": email})
    print(user_profiles)
    user_profiles["_id"] = str(user_profiles["_id"])
    user_profiles["uid"] = uid

    # email = request.headers.get('email')
    if not user_profiles:
        return jsonify({"error": "Profile not found"}), 404

    return jsonify(user_profiles), 200


@app.route("/profile_img", methods=["POST"])
def profile_img():
    # Retrieve email from request headers or wherever it's stored
    collection1 = db["login_info"]
    collection = db["profile_info"]

    token = request.form.get("token")
    image = request.files["photo"]
    res_uid1 = collection1.find_one({"token": token})

    uid = res_uid1["uid"]

    options = {"invalidate": True, "overwrite": True}
    if image:
        uploaded_image = cloudinary.uploader.upload(
            image, public_id="profile/" + uid + ".png", options=options
        )
        image.seek(0)
        public_url = uploaded_image["secure_url"]
        collection.update_one(
            {"email": res_uid1["username"]},
            {"$set": {"profile_picture_url": public_url}},
        )

        image.save(os.path.join("profile_dp/", uid + ".jpg"))
        image.seek(0)
        # x=get_base64(image)

    # print(email)
    # user_profiles=collection.find_one({"email":email})
    # print(user_profiles)
    # user_profiles["_id"]=str(user_profiles["_id"])
    # email = request.headers.get('email')
    # if not user_profiles:
    #     return jsonify({'error': 'Profile not found'}), 404

    return jsonify({"message": "profile_uploaded_success"}), 200


@app.route("/get_reports", methods=["GET"])
def get_reports():

    collection_profiles = db["children_info"]
    matched_profiles = db["matching_info"]
    collection1 = db["login_info"]
    # Parse query parameters for search and filtering
    token = request.args.get("token")
    search_query = request.args.get("search_query")
    gender = request.args.get("gender")
    min_age = request.args.get("min_age")
    max_age = request.args.get("max_age")
    min_height = request.args.get("min_height")
    max_height = request.args.get("max_height")
    min_weight = request.args.get("min_weight")
    max_weight = request.args.get("max_weight")
    min_last_seen_time = request.args.get("min_last_seen_time")
    max_last_seen_time = request.args.get("max_last_seen_time")
    is_matched = request.args.get("is_matched")
    sort_field = request.args.get("sort_field")
    sort_order = request.args.get("sort_order")
    record_type = request.args.get("record_type")
    state = request.args.get("state")
    temp_sort = "_id"
    if token:
        res_uid1 = collection1.find_one({"token": token})
        # uid=res_uid1["uid"]
        email = res_uid1["username"]

    if is_matched:
        is_matched = bool(int(is_matched))
    # occupation = request.args.get('occupation')
    # Add more filter parameters as needed

    # Construct the query based on filters
    query = {}
    if sort_field:
        temp_sort = sort_field
    if search_query:
        query["$or"] = [
            {"name": {"$regex": f".*{search_query}.*", "$options": "i"}},
            {"last_seen_location": {"$regex": f".*{search_query}.*", "$options": "i"}},
        ]
    if gender:
        query["gender"] = gender
    if min_age or max_age:
        query["age"] = {}  # Create a nested dictionary for date of birth range query
        if min_age:
            query["age"]["$gte"] = int(min_age)
        if max_age:
            query["age"]["$lte"] = int(max_age)
    if min_height or max_height:
        query["height"] = {}  # Create a nested dictionary for date of birth range query
        if min_height:
            query["height"]["$gte"] = int(min_height)
        if max_height:
            query["height"]["$lte"] = int(max_height)
    if min_weight or max_weight:
        query["weight"] = {}  # Create a nested dictionary for date of birth range query
        if min_weight:
            query["weight"]["$gte"] = int(min_weight)
        if max_weight:
            query["weight"]["$lte"] = int(max_weight)
    if min_last_seen_time or max_last_seen_time:
        query["last_seen_time"] = (
            {}
        )  # Create a nested dictionary for last seen time range query
        if min_last_seen_time:
            query["last_seen_time"]["$gte"] = datetime.strptime(
                min_last_seen_time, "%Y-%m-%d"
            )
        if max_last_seen_time:
            query["last_seen_time"]["$lte"] = datetime.strptime(
                max_last_seen_time, "%Y-%m-%d"
            )
    # if is_matched is not None:
    #     query['is_matched'] = bool(is_matched)
    if record_type:
        query["email"] = email
    if state:
        query["state"] = state

        # query['$or'] = [{'full_name': {'$regex': search_query, '$options': 'i'}}, {'address': {'$regex': search_query, '$options': 'i'}}]
    # if gender:
    #     query['gender'] = gender
    # if occupation:
    #     query['occupation'] = occupation

    user_reports = list(
        collection_profiles.find(query).sort(
            temp_sort, -1 if sort_order == "desc" else 1
        )
    )
    matched_profiles = list(matched_profiles.find({"matched": True}))
    # print(user_reports,matched_profiles)
    for i in user_reports:
        i["_id"] = str(i["_id"])
        i["last_seen_time"] = str(i["last_seen_time"])
        i["matched"] = False
        # i["base64"]=get_base64(r"training"+"\\"+"NKfotAlsifZ1eqa5QhRmfBkoOMV2_Vara"+"\\1.jpg")
        for j in matched_profiles:
            if i["images"] == j["child_id"]:

                i["matched"] = True
                i["helper_profile_email"] = j["helper_profile"]["email"]
                i["helper_full_name"] = j["helper_full_name"]
                i["helper_phone"] = j["helper_phone"]
                i["matched_location"] = j["location"]
                break
    matched = []
    not_matched = []
    for i in user_reports:
        if i["matched"] == True:
            matched.append(i)
        else:
            not_matched.append(i)
    print(matched)
    if is_matched == True:
        print("matched", matched)
        return jsonify({"reports": list(matched)}), 200
    elif is_matched == False:
        print("not_matched", not_matched)
        return jsonify({"reports": list(not_matched)}), 200

    return jsonify({"reports": list(user_reports)}), 200


@app.route("/predict", methods=["POST"])
def predict():
    collection = db["matching_info"]
    child_profile = db["children_info"]
    collection2 = db["profile_info"]
    collection1 = db["login_info"]
    token = request.form.get("token")
    lat = request.form.get("lat")
    lon = request.form.get("lon")
    image = request.files["photo"]
    temp_session = {"token": token}
    existing_session = collection1.find_one(temp_session)
    uid = existing_session["uid"]

    image_loc = save_photo_matching(image, uid)
    email = existing_session["username"]
    helper_profile = collection2.find_one({"email": email})
    helper_phone = helper_profile["phone_number"]
    helper_full_name = helper_profile["full_name"]
    x = predict_img(image_loc)

    # res=profile.find_one({"child_name":child_name})

    # print(token,session)
    # Verify login before allowing logout
    # if existing_session:
    #     collection.delete_one(temp_session)
    print(not (x == "No image matched_0" or x == "No face found_0"))
    if not (x == "No image matched_0" or x == "No face found_0"):
        c = x.split("_")
        temp_child = {"images": x}
        child_name = c[1]

        res = child_profile.find_one(temp_child)
        child_age = res["age"]
        child_description = res["description"]
        # email=res["email"]
        # parent_profile=db["profile_info"]
        mobile = res["alternate_mobile"]
        res = {
            "image": image_loc,
            "email": email,
            "helper_profile": helper_profile,
            "helper_full_name": helper_full_name,
            "helper_phone": helper_phone,
            "child_id": x,
            "matched": True,
            "location": [lat, lon],
        }
        try:
            collection.insert_one(res)
        except:
            pass
        send_email_to_parent(
            email,
            child_name,
            child_age,
            child_description,
            lat,
            lon,
            helper_full_name,
            helper_phone,
        )
        # send_sms_to_parent(child_name,child_age,lat,lon,helper_full_name,helper_phone,mobile)

        return (
            jsonify(
                {
                    "message": "Face Recognition done",
                    "name": child_name,
                    "age": child_age,
                    "child_description": child_description,
                    "parent_mobile": mobile,
                }
            ),
            200,
        )
    else:
        res = {
            "image": image_loc,
            "email": email,
            "helper_profile": helper_profile,
            "helper_full_name": helper_full_name,
            "helper_phone": helper_phone,
            "child_id": "Not Found",
            "matched": False,
        }
        # send_email_to_parent(email,child_name,child_age,child_description,lat,lon,helper_full_name,helper_phone)
        return jsonify({"message": "No Face matched with the records"}), 500
    # else:
    #     return jsonify({'error': 'You are not logged in.'}), 401


@app.route("/count", methods=["PUT"])
def matched_count():
    collection2 = db["children_info"]
    collection1 = db["login_info"]
    collection = db["profile_info"]

    token = request.form.get("token")
    res_uid1 = collection1.find_one({"token": token})

    uid = res_uid1["uid"]
    email = res_uid1["username"]
    print(email)
    user_profiles = collection.find_one({"email": email})
    print(user_profiles)
    user_profiles["_id"] = str(user_profiles["_id"])
    user_profiles["uid"] = uid
    total = collection2.count_documents({})
    collection3 = db["matching_info"]
    pipeline = [{"$group": {"_id": "$child_id", "count": {"$sum": 1}}}]
    results = list(collection3.aggregate(pipeline))

  

    x = {
        "total": total,
        "matched": len(results),
        "name": user_profiles["full_name"],
    }
    if "profile_picture_url" in user_profiles:
        x["profile_picture_url"]= user_profiles["profile_picture_url"]
    return jsonify(x)


@app.route("/emergency_contacts", methods=["PUT"])
def get_emergency_contacts():
    collection = db["emergency_info"]
    collection1 = db["login_info"]
    # Retrieve request data

    token = request.form.get("token")
    res_uid1 = collection1.find_one({"token": token})

    uid = res_uid1["uid"]
    email = res_uid1["username"]

    emergency_contacts = collection.find_one({"email": email})

    if not emergency_contacts:
        return jsonify({"error": "Emergency Contacts not found"}), 404

    emergency_contacts["_id"] = str(emergency_contacts["_id"])
    return jsonify(emergency_contacts), 200


@app.route("/update_emergency_contacts", methods=["GET"])
def update_emergency_contacts():
    collection = db["emergency_info"]
    collection1 = db["login_info"]
    # Retrieve request data

    token = request.args.get("token")
    res_uid1 = collection1.find_one({"token": token})

    uid = res_uid1["uid"]
    email = res_uid1["username"]

    name1 = request.args.get("name1")
    relation1 = request.args.get("relation1")
    phone_number1 = request.args.get("phone_number1")
    email1 = request.args.get("email1")
    name2 = request.args.get("name2")
    relation2 = request.args.get("relation2")
    phone_number2 = request.args.get("phone_number2")
    email2 = request.args.get("email2")

    updated_fields = {}
    if name1:
        updated_fields["name1"] = name1
    if relation1:
        updated_fields["relation1"] = relation1
    if phone_number1:
        updated_fields["phone_number1"] = phone_number1
    if email1:
        updated_fields["email1"] = email1
    if name2:
        updated_fields["name2"] = name2
    if email2:
        updated_fields["email2"] = email2
    if phone_number2:
        updated_fields["phone_number2"] = phone_number2
    if relation2:
        updated_fields["relation2"] = relation2
    x = collection.find_one({"email": email})

    if x:
        result = collection.update_one({"email": email}, {"$set": updated_fields})
        if result:
            return jsonify({"message": "Emergency contacts updated successfully."}), 200
        else:
            return jsonify({"error": "Failed to update emergency contacts."}), 500

    else:
        updated_fields["email"] = email
        updated_fields["uid"] = uid
        result = collection.insert_one(updated_fields)
        if result:
            return jsonify({"message": "Emergency contacts created successfully."}), 200
        else:
            return jsonify({"error": "Failed to create emergency contacts."}), 500

    # Validate input data

    # Construct update query


def save_photo_matching(photo, uid):
    if photo:
        x = os.getcwd()
        filename = secure_filename(photo.filename)
        dest_directory = os.path.join(x, "history", uid)
        os.makedirs(dest_directory, exist_ok=True)
        count = str(len(list(os.scandir(dest_directory))))
        file_loc = os.path.join(dest_directory, count + ".jpg")
        photo.save(file_loc)
        return file_loc


def save_photo(photo, uid):
    if photo:
        x = os.getcwd()
        filename = secure_filename(photo.filename)
        dest_directory = os.path.join(x, "profile")
        os.makedirs(dest_directory, exist_ok=True)
        file_loc = os.path.join(dest_directory, uid + ".jpg")
        photo.save(os.path.join(dest_directory, uid + ".jpg"))
        return file_loc
    else:
        return None


#
def save_images(images, uid, name):
    x = os.getcwd()
    count = 0
    # cloudinary.uploader.upload("https://upload.wikimedia.org/wikipedia/commons/a/ae/Olympic_flag.jpg",
    # public_id = "test/olympic_flag")
    # print("hi")
    for file in images:
        count += 1
        destination_directory = os.path.join(x, "training", uid + "_" + name)
        os.makedirs(destination_directory, exist_ok=True)
        print(str(count) + ".png")
        cloudinary.uploader.upload(
            file, public_id="training/" + uid + "_" + name + "/" + str(count) + ".png"
        )
        file.seek(0)
        file.save(os.path.join(destination_directory, str(count) + ".jpg"))
    return uid + "_" + name


def get_base64(image):

    with open(image, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode("utf-8")
        return encoded_string


@app.route("/incident_hour_distribution", methods=["GET"])
def get_incident_hour_distribution():
    # Query MongoDB to get distribution of missing child incidents by time of day
    incident_time_distribution = db["children_info"].aggregate(
        [{"$group": {"_id": {"$hour": "$last_seen_time"}, "count": {"$sum": 1}}}]
    )
    incident_time_distribution_data = {
        "res": [
            {"hour": item["_id"], "count": item["count"]}
            for item in incident_time_distribution
        ]
    }
    return jsonify(incident_time_distribution_data)


@app.route("/incident_month_distribution", methods=["GET"])
def get_incident_month_distribution():
    # Query MongoDB to get distribution of missing child incidents by time of day
    incident_time_distribution = db["children_info"].aggregate(
        [{"$group": {"_id": {"$month": "$last_seen_time"}, "count": {"$sum": 1}}}]
    )
    incident_time_distribution_data = {
        "res": [
            {"month": item["_id"], "count": item["count"]}
            for item in incident_time_distribution
        ]
    }
    return jsonify(incident_time_distribution_data)


@app.route("/incident_year_distribution", methods=["GET"])
def get_incident_year_distribution():
    # Query MongoDB to get distribution of missing child incidents by time of day
    incident_time_distribution = db["children_info"].aggregate(
        [{"$group": {"_id": {"$year": "$last_seen_time"}, "count": {"$sum": 1}}}]
    )
    incident_time_distribution_data = {
        "res": [
            {"year": item["_id"], "count": item["count"]}
            for item in incident_time_distribution
        ]
    }
    return jsonify(incident_time_distribution_data)


@app.route("/incident_month_distribution_year", methods=["PUT"])
def get_incident_month_distribution_year():
    year = int(request.form.get("year"))
    # Query MongoDB to get distribution of missing child incidents by month for a specific year
    incident_month_distribution = db["children_info"].aggregate(
        [
            {"$match": {"$expr": {"$eq": [{"$year": "$last_seen_time"}, year]}}},
            {"$group": {"_id": {"$month": "$last_seen_time"}, "count": {"$sum": 1}}},
        ]
    )

    # incident_month_distribution = db['children_info'].find({"last_seen_time": {"$gte": datetime(year, 1, 1), "$lt": datetime(year + 1, 1, 1)}})
    # incident_month_distribution["_id"]=str(incident_month_distribution['_id'])
    # incident_month_distribution_data = {"res": [{"month": item["last_seen_time"].month, "count": 1} for item in incident_month_distribution]}
    incident_month_distribution_data = {
        "res": [
            {"month": item["_id"], "count": item["count"]}
            for item in incident_month_distribution
        ]
    }
    return jsonify(incident_month_distribution_data)


@app.route("/incident_date_distribution", methods=["GET"])
def get_incident_date_distribution():
    # Query MongoDB to get distribution of missing child incidents by date of the month
    incident_date_distribution = db["children_info"].aggregate(
        [
            {"$project": {"dayOfMonth": {"$dayOfMonth": "$last_seen_time"}}},
            {"$group": {"_id": "$dayOfMonth", "count": {"$sum": 1}}},
        ]
    )

    # Convert day number to actual day name
    incident_date_distribution_data = {
        "res": [
            {"date": item["_id"], "count": item["count"]}
            for item in incident_date_distribution
        ]
    }

    return jsonify(incident_date_distribution_data)


@app.route("/incident_day_distribution", methods=["GET"])
def get_incident_day_distribution():
    # Query MongoDB to get distribution of missing child incidents by day of the week
    incident_day_distribution = db["children_info"].aggregate(
        [
            {"$project": {"dayOfWeek": {"$dayOfWeek": "$last_seen_time"}}},
            {"$group": {"_id": "$dayOfWeek", "count": {"$sum": 1}}},
        ]
    )

    # Convert day number to actual day name
    days_of_week = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]
    incident_day_distribution_data = {
        "res": [
            {"day": item["_id"] - 1, "count": item["count"]}
            for item in incident_day_distribution
        ]
    }

    return jsonify(incident_day_distribution_data)


@app.route("/incident_location_distribution", methods=["GET"])
def get_incident_location_distribution():
    # Query MongoDB to get distribution of missing child incidents by location type
    incident_location_distribution = db["missing_children"].aggregate(
        [{"$group": {"_id": "$location_type", "count": {"$sum": 1}}}]
    )
    print(incident_location_distribution)
    incident_location_distribution_data = {
        "res": [
            {"location_type": item["_id"], "count": item["count"]}
            for item in incident_location_distribution
        ]
    }
    return jsonify(incident_location_distribution_data)


@app.route("/age_distribution_found_vs_missing", methods=["GET"])
def get_age_distribution_found_vs_missing():
    # Query MongoDB to get age distribution of found children vs. still missing children
    # age_distribution = db['missing_children'].aggregate([
    #     {"$group": {"_id": {"status": "$status", "age_group": "$age_group"}, "count": {"$sum": 1}}}
    # ])

    age_distribution_cursor = db["children_info"].aggregate(
        [
            {"$project": {"age": {"$toInt": "$age"}}},
            {
                "$group": {
                    "_id": {
                        "age_group": {
                            "$concat": [
                                {
                                    "$toString": {
                                        "$multiply": [
                                            {"$trunc": {"$divide": ["$age", 10]}},
                                            10,
                                        ]
                                    }
                                },
                                "-",
                                {
                                    "$toString": {
                                        "$add": [
                                            {
                                                "$multiply": [
                                                    {
                                                        "$trunc": {
                                                            "$divide": ["$age", 10]
                                                        }
                                                    },
                                                    10,
                                                ]
                                            },
                                            9,
                                        ]
                                    }
                                },
                            ]
                        }
                    },
                    "count": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "status": "$_id.status",
                    "age_group": "$_id.age_group",
                    "count": 1,
                }
            },
        ]
    )

    age_distribution_data = [
        {"age_group": item["age_group"], "count": item["count"]}
        for item in age_distribution_cursor
    ]

    print(age_distribution_data)
    # age_distribution = {}
    # for result in age_distribution_cursor:
    #     age_distribution[result['age_group']] = {"count": result['count']}

    # print(age_distribution)
    # age_distribution_data = {"res": [{"status": item["_id"]["status"], "age_group": item["_id"]["age_group"], "count": item["count"]} for item in age_distribution]}
    return jsonify(age_distribution_data)


@app.route("/age_distribution", methods=["GET"])
def get_age_distribution():
    age_distribution_cursor = db["children_info"].aggregate(
        [
            {"$project": {"age": {"$toInt": "$age"}}},
            {
                "$group": {
                    "_id": {
                        "age_group": {
                            "$concat": [
                                {
                                    "$toString": {
                                        "$multiply": [
                                            {"$trunc": {"$divide": ["$age", 10]}},
                                            10,
                                        ]
                                    }
                                },
                                "-",
                                {
                                    "$toString": {
                                        "$add": [
                                            {
                                                "$multiply": [
                                                    {
                                                        "$trunc": {
                                                            "$divide": ["$age", 10]
                                                        }
                                                    },
                                                    10,
                                                ]
                                            },
                                            9,
                                        ]
                                    }
                                },
                            ]
                        }
                    },
                    "count": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "status": "$_id.status",
                    "age_group": "$_id.age_group",
                    "count": 1,
                }
            },
        ]
    )

    age_distribution_data_all = [
        {"age_group": item["age_group"], "count": item["count"]}
        for item in age_distribution_cursor
    ]

    # Query MongoDB to get age distribution of found children vs. still missing children
    # age_distribution = db['missing_children'].aggregate([
    #     {"$group": {"_id": {"status": "$status", "age_group": "$age_group"}, "count": {"$sum": 1}}}
    # ])

    age_distribution_cursor = db.children_info.aggregate(
        [
            {"$match": {"images": {"$in": db.matching_info.distinct("child_id")}}},
            {
                "$project": {
                    "age": {"$toInt": "$age"},
                }
            },
            {
                "$group": {
                    "_id": {
                        "age_group": {
                            "$concat": [
                                {
                                    "$toString": {
                                        "$multiply": [
                                            {"$trunc": {"$divide": ["$age", 10]}},
                                            10,
                                        ]
                                    }
                                },
                                "-",
                                {
                                    "$toString": {
                                        "$add": [
                                            {
                                                "$multiply": [
                                                    {
                                                        "$trunc": {
                                                            "$divide": ["$age", 10]
                                                        }
                                                    },
                                                    10,
                                                ]
                                            },
                                            9,
                                        ]
                                    }
                                },
                            ]
                        }
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$project": {"_id": 0, "age_group": "$_id.age_group", "count": 1}},
        ]
    )

    age_distribution_data_matched = [
        {"age_group": item["age_group"], "count": item["count"]}
        for item in age_distribution_cursor
    ]

    age_distribution_data_temp = {
        item["age_group"]: item["count"] for item in age_distribution_data_all
    }
    

    for item in age_distribution_data_matched:
        age_group = item['age_group']
        if age_group in age_distribution_data_temp:
            age_distribution_data_temp[age_group] -= item['count']
    age_distribution_data_unmatched=[{"age_group":key,"count":value} for key,value in age_distribution_data_temp.items()]

    res={"matched":age_distribution_data_matched,"unmatched":age_distribution_data_unmatched,"all":age_distribution_data_all}
    # print(age_distribution_data)
    return jsonify(res)


if __name__ == "__main__":
    app.run(debug=True)
