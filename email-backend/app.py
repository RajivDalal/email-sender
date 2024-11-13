import io
from flask import Flask, request
from google_sheets import read_google_sheet
import csv

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Flask!"

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
    except Exception as e:
        return {"error": str(e)}, 500

    return {'message': "CSV uploaded successfully", 'data': data}, 200

@app.route('/fetch_google_sheet', methods=['GET'])
def fetch_google_sheet():
    sheet_id = request.args.get('sheet_id')
    range_name = request.args.get('range_name')

    if not sheet_id or not range_name:
        return {"error": "Missing sheet_id or range_name"}, 400
    
    try:
        raw_data = read_google_sheet(sheet_id,range_name)

        if not raw_data:
            return {"error": "Data not Sufficient"}, 404

        headers = raw_data[0]
        data = [dict(zip(headers, row)) for row in raw_data[1:]]

    except Exception as e:
        return {"error": str(e)}, 500

    return {"message": "Data fetched Sucecsfully", "data": data}, 200

if __name__ == "__main__":
    app.run(debug=True)
