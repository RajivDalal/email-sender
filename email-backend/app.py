from pymongo import MongoClient
from flask import Flask, request
import csv
import io
import gspread
import os
from dotenv import load_dotenv

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

@app.route("/test_db", methods = ['GET'])
def test_db():
    try:
        email_data_collection.insert_one({"test": "Connection Successful"})
        return {"message": "Database connection successful!"}, 200
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
        decoded_file = io.StringIO(file.stream.read().decode('utf-8'))
        csv_read = csv.DictReader(decoded_file)
        for row in csv_read:
            data.append(row)

        if data:
            email_data_collection.insert_many(data)

    except Exception as e:
        return {"error": str(e)}, 500

    return {'message': "CSV uploaded successfully", 'data': data}, 200

@app.route('/fetch_google_sheet', methods=['GET'])
def fetch_google_sheet():
    sheet_url = request.args.get('sheet_url')

    if not sheet_url:
        return {"error": "Missing sheet_url"}, 400
    
    try:

        gc = gspread.service_account(filename="credentials.json")
        sheet = gc.open_by_url(sheet_url)
        worksheet = sheet.get_worksheet(0)

        data = worksheet.get_all_records()

        if data:
            email_data_collection.insert_many(data)
        else:
            return {"error": "Data not Sufficient"}, 404

    except Exception as e:
        return {"error": str(e)}, 500

    return {"message": "Data fetched Sucecsfully", "data": data}, 200

if __name__ == "__main__":
    app.run(debug=True)
