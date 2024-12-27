# **Automated Video Upload from OneDrive to YouTube**

## **Overview**

This project automates the process of downloading video files from OneDrive and uploading them to YouTube. It utilizes the Microsoft Graph API to access OneDrive and the YouTube Data API to upload videos. The script is designed to simplify content sharing for users who need to manage video uploads between these two platforms.

## **Prerequisites**

Before running the script, ensure you have the following:
- Python 3.6 or higher installed.
- A Microsoft OneDrive account and a YouTube channel.
- API credentials for both Microsoft and Google services.

## **Generate API Credentials**

### **1. Microsoft API Credentials (Microsoft Graph API)**

To use the Microsoft Graph API and access OneDrive, you need to register an application in the Azure portal and generate API credentials.

#### **Steps to Generate Microsoft API Credentials:**

1. **Go to Azure Portal**: Open the Azure portal at [Azure Portal](https://portal.azure.com/).
2. **Register an Application**:
    - Navigate to **Azure Active Directory** > **App registrations** > **New registration**.
    - Enter a name for the application (e.g., "OneDrive Video Uploader").
    - Choose **Accounts in any organizational directory and personal Microsoft accounts** for supported account types.
    - Set the **Redirect URI** to `http://localhost:8080` for local development setup.
    - Click **Register**.
3. **Create a Client Secret**:
    - Under the application registration page, go to **Certificates & Secrets** > **New client secret**.
    - Add a description (e.g., "API secret") and set an expiry period.
    - Copy the **Value** of the secret (this is your `CLIENT_SECRET`).
4. **Get Your Application ID**:
    - Under the **Overview** tab, copy the **Application (client) ID**.
5. **API Permissions**:
    - Go to **API Permissions** > **Add a permission** > **Microsoft Graph** > **Delegated permissions**.
    - Add `Files.ReadWrite.All` and `User.Read` for OneDrive access.
6. **Configure Redirect URI**:
    - In the **Authentication** section, ensure the Redirect URI is configured as `http://localhost:8080`.

Now, you have the **APPLICATION_ID** and **CLIENT_SECRET** which will be used to configure the script.

---

### **2. Google API Credentials (YouTube Data API)**

To interact with YouTube and upload videos, you need to set up OAuth 2.0 credentials via the Google Developer Console.

#### **Steps to Generate Google API Credentials:**

1. **Go to Google Cloud Console**: Open the Google Cloud Console at [Google Cloud Console](https://console.cloud.google.com/).
2. **Create a New Project**:
    - Click on the **Select a Project** dropdown and then click **New Project**.
    - Name the project (e.g., "YouTube Video Uploader").
3. **Enable YouTube Data API**:
    - In the **API & Services** > **Library**, search for **YouTube Data API v3** and enable it.
4. **Create OAuth 2.0 Credentials**:
    - Navigate to **APIs & Services** > **Credentials** > **Create Credentials** > **OAuth 2.0 Client IDs**.
    - Choose **Web application** as the application type.
    - Add **Authorized redirect URIs**: `http://localhost:8080` for local development.
    - Once the credentials are created, copy the **Client ID** and **Client Secret**.
5. **Download Client Secret File**:
    - After creating the credentials, download the **client_secret.json** file and save it in your project directory.

---

## **Configure the Script**

### **1. Set Up Environment Variables**

Create a `.env` file in your project directory with the following content:

APPLICATION_ID=<Your Microsoft Application ID> CLIENT_SECRET=<Your Microsoft Client Secret> YOUTUBE_CLIENT_ID=<Your YouTube Client ID> YOUTUBE_CLIENT_SECRET=<Your YouTube Client Secret>


Replace the placeholders with the values obtained in the previous steps.

### **2. Configure OneDrive Folder and YouTube Channel**

#### **OneDrive Folder Configuration:**

The script downloads video files from a specific OneDrive folder. By default, it checks the root folder, but you can modify the `folder_id` variable in the script to target a specific folder.

To configure this:
1. Use **Microsoft Graph Explorer** or a similar tool to find the **folder ID** of the OneDrive folder you want to target.
2. Update the `folder_id` variable in the script with the desired folder's ID.

#### **YouTube Channel Configuration:**

The script will upload videos to your authenticated YouTube account by default. The YouTube credentials (Client ID and Client Secret) in the `.env` file handle the OAuth authentication process. Ensure that the correct Google account is linked to your desired YouTube channel during authentication.

---

## **Running the Script**

### **1. Install Dependencies**

Install the required Python dependencies by running:

```bash
pip install -r requirements.txt
----

### ** Ensure the requirements.txt file includes the following libraries:
msal
httpx
google-auth
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
dotenv
mimetypes


2. Execute the Script
Run the script using Python:
python script.py

The script will:

Authenticate with Microsoft and Google services.
Scan the specified OneDrive folder for video files.
Download the found videos to a local downloads folder.
Upload the videos to your YouTube channel with predefined metadata.
Clean up the downloads folder after the upload process.

