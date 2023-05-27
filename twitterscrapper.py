import asyncio
from twscrape import AccountsPool, API, gather
from twscrape.logger import set_log_level
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import datetime  
import pytz 
from dotenv import load_dotenv
import os


# Load environment variables from .env file
load_dotenv()


async def main():
    set_log_level("DEBUG")

    pool = AccountsPool()  
    await pool.add_account(os.getenv("ACCOUNT1_USERNAME"), os.getenv("ACCOUNT1_PASSWORD"), os.getenv("ACCOUNT1_EMAIL"), os.getenv("ACCOUNT1_EMAIL_PASSWORD"))
    await pool.add_account(os.getenv("ACCOUNT2_USERNAME"), os.getenv("ACCOUNT2_PASSWORD"), os.getenv("ACCOUNT2_EMAIL"), os.getenv("ACCOUNT2_EMAIL_PASSWORD"))
    await pool.login_all()

    api = API(pool)

    print("Setting up Google Sheets...")

    # You need to get your credentials from the Google Developer Console with the Google Sheets API enabled
    # Save it as client_secret.json in the same directory as this script
    creds = service_account.Credentials.from_service_account_file('client_secret.json')
    service = build('sheets', 'v4', credentials=creds)
    # Define the Google Sheet ID here (the long string in the URL of the spreadsheet)
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    range_name = 'Sheet1!A1:E1'

    try:
        service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        print("Google Sheets API is working.")
    except Exception as e:
        print(f"Google Sheets API is not working: {e}")
        return

    # Add headers to the Google Sheet
    headers = ['Tweet ID', 'Date and Time', 'Username', 'Content']
    body = {'values': [headers]}
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id, range=range_name,
        valueInputOption='USER_ENTERED', body=body).execute()

    print("Scraping tweets and replies from 1st account...")
    await api.user_by_id(os.getenv("TARGET1_ID"))  
    await api.user_by_login(os.getenv("TARGET1_LOGIN"))  
    tweets = await gather(api.user_tweets_and_replies(os.getenv("TARGET1_ID"), limit=20))  


    rows = [[str(tweet.id), tweet.date.isoformat(), tweet.user.username, tweet.rawContent] for tweet in tweets]
    body = {'values': rows}
    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id, range=range_name,
        valueInputOption='USER_ENTERED', body=body).execute()

    print("Scraping tweets and replies from 2nd account since May 5...")
    await api.user_by_id(os.getenv("TARGET2_ID"))  
    await api.user_by_login(os.getenv("TARGET2_LOGIN"))  
    tweets = await gather(api.user_tweets_and_replies(os.getenv("TARGET2_ID"), limit=20))  

    rows = [[str(tweet.id), tweet.date.isoformat(), tweet.user.username, tweet.rawContent] for tweet in tweets if tweet.date >= datetime.datetime(2023, 5, 5, tzinfo=pytz.UTC)]
    body = {'values': rows}
    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id, range=range_name,
        valueInputOption='USER_ENTERED', body=body).execute()

    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())

