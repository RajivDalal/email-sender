import io
from flask import Flask, request
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

if __name__ == "__main__":
    app.run(debug=True)
