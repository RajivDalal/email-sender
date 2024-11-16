from pymongo import MongoClient
from flask import Flask, request
import csv
import io
import gspread
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime

from google_auth_oauthlib.flow import Flow
from utils import credentials_to_dict, dict_to_credentials
import jwt

# Load env variables
load_dotenv()

# MongoDB connection
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client.email_sender
email_data_collection = db.email_data
users_collection = db.users
schedules_collection = db.schedules

# Flask app
app = Flask(__name__)

#Testing routes
@app.route("/")
def home():
    return "Hello, Flask!"

@app.route("/delete_db_data", methods = ['DELETE'])
def delete_db_data():
    try:
        email_data_collection.delete_many({})
        return {"message": "Database deletion successful!"}, 200
    except Exception as e:
        return {"error": str(e)}, 500

#Auth routes
@app.route("/authorize", methods = ['GET'])
def authorize():

    SCOPES = ["openid","https://www.googleapis.com/auth/gmail.send","https://www.googleapis.com/auth/userinfo.email"]

    flow = Flow.from_client_secrets_file(
            'client_secret.json',
            scopes=SCOPES,
            redirect_uri='http://localhost:5000/oauth2callback'
            )

    auth_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true')

    return {"auth_url": auth_url}, 200

@app.route('/oauth2callback', methods=['GET'])
def oauth2callback():
    try:
        SCOPES = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/gmail.send'
        ]
        flow = Flow.from_client_secrets_file(
            'client_secret.json',
            scopes=SCOPES,
            redirect_uri='http://localhost:5000/oauth2callback'
        )
        flow.fetch_token(authorization_response=request.url)

        credentials = flow.credentials

        # Debugging
        print(f"Credentials: {credentials}")
        print(f"ID Token: {credentials.id_token}")

        # Decode ID token
        email = None
        if credentials.id_token:
            id_token_decoded = jwt.decode(credentials.id_token, options={"verify_signature": False})
            email = id_token_decoded.get('email')

        if not email:
            return {"error": "Unable to retrieve email from credentials"}, 400

        # Save to MongoDB
        users_collection.update_one(
            {'email': email},
            {'$set': {
                'email': email,
                'credentials': credentials_to_dict(credentials)
            }},
            upsert=True
        )

        return {"message": "Authorization successful", "email": email}, 200
    except Exception as e:
        print(f"Error during OAuth2 callback: {e}")
        return {"error": "Internal Server Error", "details": str(e)}, 500

#Upload CSV/Google Sheets
@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return {'error': 'File not uploaded'}, 400

    file = request.files['file']

    if not file.filename.endswith('.csv'):
        return {'error': 'Invalid File Type'}, 400

    data = []
    try:
        
        batch_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        decoded_file = io.StringIO(file.stream.read().decode('utf-8'))
        csv_read = csv.DictReader(decoded_file)

        for row in csv_read:
            row['batch_id'] = batch_id
            row['uploaded_at'] = timestamp
            data.append(row)

        if data:
            email_data_collection.insert_many(data)

    except Exception as e:
        return {"error": str(e)}, 500

    return {'message': "CSV uploaded successfully"}, 200

@app.route('/fetch_google_sheet', methods=['GET'])
def fetch_google_sheet():
    sheet_url = request.args.get('sheet_url')

    if not sheet_url:
        return {"error": "Missing sheet_url"}, 400
    
    try:

        batch_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        gc = gspread.service_account(filename="credentials.json")
        sheet = gc.open_by_url(sheet_url)
        worksheet = sheet.get_worksheet(0)

        data = worksheet.get_all_records()

        for row in data:
            row['batch_id'] = batch_id
            row['uploaded_at'] = timestamp

        if data:
            email_data_collection.insert_many(data) 
        else:
            return {"error": "Data not Sufficient"}, 404

    except Exception as e:
        return {"error": str(e)}, 500

    return {"message": "Data fetched Sucecsfully"}, 200

#API Routes
@app.route('/api/data-batch', methods=['GET'])
def get_data_by_batch():
    batch_id = request.args.get('batch_id')

    if not batch_id:
        return {"error": "Missing batch_id"}, 400

    try:
        data = list(email_data_collection.find({"batch_id": batch_id}, {"_id": 0}))
        if not data:
            return {"message": "No data found for the given batch_id"}, 404

    except Exception as e:
        return {"error": str(e)}, 500

    return {"message": "Data retrieved successfully", "data": data}, 200

if __name__ == "__main__":
    app.run(debug=True)
