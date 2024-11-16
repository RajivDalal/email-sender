from pymongo import MongoClient
from flask import Flask, request
import csv
import io
import gspread
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime

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
<<<<<<< HEAD

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
=======
>>>>>>> refs/remotes/origin/main

if __name__ == "__main__":
    app.run(debug=True)
