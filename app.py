import os
import webbrowser
import msal
import httpx
import json
from pathlib import Path
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import mimetypes
import time

# Constants
MS_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0/"
TOKEN_FILE = 'onedrive_token.json'
CLIENT_SECRETS_FILE = "client_secret.json"
YOUTUBE_TOKEN_FILE = 'youtube_token.json'
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
DOWNLOADS_FOLDER = Path('downloads')
LOG_FILE = 'actions.log'  # Log file for storing logs

# Log function with timestamp (also writes to a log file)
def log_action(action, message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    log_message = f"[{timestamp}] {action}: {message}"

    # Print to console
    print(log_message)

    # Write to log file
    try:
        with open(LOG_FILE, 'a') as log:
            log.write(log_message + "\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")

# Function to download a file from OneDrive
def download_file(headers, file_id, file_name):
    url = f'{MS_GRAPH_BASE_URL}/me/drive/items/{file_id}/content'
    response = httpx.get(url, headers=headers)

    if response.status_code == 302:
        # 302 file found, get the download location
        download_location = response.headers['Location']
        response_file_download = httpx.get(download_location)

        with open(file_name, 'wb') as file:
            file.write(response_file_download.content)
        log_action("Download", f'File "{file_name}" downloaded successfully')
    else:
        log_action("Download Error", f'Failed to download file with ID {file_id}. {response.text}')

# Recursive function to check all folders and subfolders for video files
def check_folders_for_videos(headers, folder_id, target_dir):
    url = f'{MS_GRAPH_BASE_URL}/me/drive/items/{folder_id}/children'
    response = httpx.get(url, headers=headers)
    video_files_found = False

    if response.status_code == 200:
        files = response.json()['value']
        for file in files:
            if 'file' in file:
                # Check if the file is a video
                if is_video_file(file['name']):
                    log_action("Found Video", f"Found video file: {file['name']}")
                    download_file(headers, file['id'], target_dir / file['name'])
                    video_files_found = True
            elif 'folder' in file:
                # If the item is a folder, recursively check for videos inside it
                log_action("Folder Check", f"Checking folder: {file['name']}")
                video_files_found |= check_folders_for_videos(headers, file['id'], target_dir)

    else:
        log_action("Folder Listing Error", f'Failed to list folder {folder_id}: {response.status_code}')
    
    return video_files_found

# Function to get access token using MSAL
def get_access_token(application_id, client_secret, scopes):
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)
        if 'access_token' in token_data:
            return token_data['access_token']
    
    client = msal.ConfidentialClientApplication(
        client_id=application_id,
        client_credential=client_secret,
        authority='https://login.microsoftonline.com/consumers/'
    )
    auth_request_url = client.get_authorization_request_url(scopes)
    webbrowser.open(auth_request_url)

    authorization_code = input('Enter the authorization code: ')

    token_response = client.acquire_token_by_authorization_code(
        code=authorization_code,
        scopes=scopes
    )

    if "access_token" in token_response:
        # Save the token to a file for future use
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_response, f)
        log_action("Authentication", "MS Graph API token saved successfully")
        return token_response["access_token"]
    else:
        raise Exception(f"Failed to acquire access token: {token_response.get('error_description', 'Unknown error')}")

# Function to filter for video files based on their extensions
def is_video_file(file_name):
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    return any(file_name.lower().endswith(ext) for ext in video_extensions)

# Function to authenticate and get the API client for YouTube
def authenticate_youtube():
    credentials = None

    # Check if token file exists and load credentials from it
    if os.path.exists(YOUTUBE_TOKEN_FILE):
        try:
            with open(YOUTUBE_TOKEN_FILE, 'r') as token:
                token_data = json.load(token)
                credentials = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            log_action("Error", f"Error loading token file: {e}")

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())  # Refresh the expired token
            log_action("Authentication", "YouTube API token refreshed.")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)

        with open(YOUTUBE_TOKEN_FILE, 'w') as token:
            token_data = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
                "expiry": credentials.expiry.isoformat()
            }
            json.dump(token_data, token)
            log_action("Authentication", "YouTube API token saved successfully")

    youtube = build("youtube", "v3", credentials=credentials)
    return youtube

# Function to upload a video to YouTube
def upload_video(youtube, video_file, title, description, category="22", privacy="private"):
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category
        },
        "status": {
            "privacyStatus": privacy
        }
    }

    mime_type, _ = mimetypes.guess_type(video_file)
    media_body = MediaFileUpload(video_file, mimetype=mime_type, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media_body
    )

    response = request.execute()
    log_action("Upload", f"Video uploaded successfully: {response['id']}")
    return response

# Function to upload all videos from the 'downloads' folder
def upload_videos_from_folder():
    youtube = authenticate_youtube()

    if not DOWNLOADS_FOLDER.exists():
        log_action("Error", "The 'downloads' folder does not exist.")
        return

    for video_file in DOWNLOADS_FOLDER.glob('*.*'):
        if video_file.is_file():
            log_action("Upload Start", f"Uploading video: {video_file.name}")
            title = video_file.stem
            description = f"Video uploaded from {video_file.name}"
            upload_video(youtube, str(video_file), title, description)

# Function to clean up the 'downloads' folder
def cleanup_downloads():
    try:
        for file in DOWNLOADS_FOLDER.glob('*.*'):
            file.unlink()
        log_action("Cleanup", "Downloads folder cleaned up successfully.")
    except Exception as e:
        log_action("Error", f"Error cleaning up the folder: {e}")

# Main function to run the complete process
def main():
    load_dotenv()  # Load environment variables from a .env file
    APPLICATION_ID = os.getenv('APPLICATION_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    SCOPES = ['User.Read', 'Files.ReadWrite.All']

    try:
        access_token = get_access_token(APPLICATION_ID, CLIENT_SECRET, SCOPES)
        headers = {'Authorization': f'Bearer {access_token}'}
        folder_id = "root"
        target_dir = DOWNLOADS_FOLDER

        target_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Download video files from OneDrive
        video_files_found = check_folders_for_videos(headers, folder_id, target_dir)
        if not video_files_found:
            log_action("Download", "No video files found in OneDrive.")

        # Step 2: Upload videos to YouTube
        upload_videos_from_folder()

        # Step 3: Clean up the downloads folder
        cleanup_downloads()

    except Exception as e:
        log_action("Error", f'Error: {e}')

if __name__ == "__main__":
    main()
