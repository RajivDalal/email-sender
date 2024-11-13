from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def read_google_sheet(sheet_id, range_name):
    creds = Credentials.from_service_account_file(
            "credentials.json", scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
            )
    service = build('sheets','v4',credentials = creds)
    sheet = service.spreadsheets()

    request = sheet.values().get(spreadsheetId=sheet_id, range=range_name)
    result = request.execute()

    return result.get('values',[])

