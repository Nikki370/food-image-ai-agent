import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# ============================================================
# CONFIGURATION
# ============================================================

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive.file"
]


# ============================================================
# GOOGLE DRIVE AUTHENTICATION
# ============================================================

def authenticate_google_drive():

    creds = None

    # --------------------------------------------------------
    # Load existing token
    # --------------------------------------------------------

    if os.path.exists(TOKEN_FILE):

        print("Found existing token.json")

        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    # --------------------------------------------------------
    # Refresh or create credentials
    # --------------------------------------------------------

    if not creds or not creds.valid:

        if (
            creds
            and creds.expired
            and creds.refresh_token
        ):

            print("Refreshing Google Drive token...")

            creds.refresh(Request())

        else:

            if not os.path.exists(CREDENTIALS_FILE):

                raise FileNotFoundError(
                    "credentials.json not found "
                    "in project root."
                )

            print(
                "Starting Google OAuth authorization..."
            )

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )

            creds = flow.run_local_server(
                port=0
            )

        # ----------------------------------------------------
        # Save token
        # ----------------------------------------------------

        with open(TOKEN_FILE, "w") as token:

            token.write(
                creds.to_json()
            )

        print(
            "token.json created successfully ✓"
        )

    # --------------------------------------------------------
    # Build Drive service
    # --------------------------------------------------------

    service = build(
        "drive",
        "v3",
        credentials=creds
    )

    print(
        "Google Drive authentication successful ✓"
    )

    return service


# ============================================================
# CREATE GOOGLE DRIVE FOLDER
# ============================================================

def create_drive_folder(
    service,
    folder_name,
    parent_folder_id=None
):

    folder_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }

    if parent_folder_id:

        folder_metadata["parents"] = [
            parent_folder_id
        ]

    folder = service.files().create(
        body=folder_metadata,
        fields="id, name"
    ).execute()

    print(
        f"Drive folder created ✓ "
        f"{folder['name']}"
    )

    print(
        f"Folder ID: {folder['id']}"
    )

    return folder["id"]


def find_file_in_drive(service, file_name, folder_id):
    query = (
        f"name = '{file_name}' "
        f"and '{folder_id}' in parents "
        f"and trashed = false"
    )

    results = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name, webViewLink)",
        pageSize=10
    ).execute()

    files = results.get("files", [])

    if files:
        return files[0]

    return None



# ============================================================
# UPLOAD FILE TO GOOGLE DRIVE
# ============================================================

def upload_file_to_drive(
    service,
    file_path,
    folder_id=None
):

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    file_name = os.path.basename(
        file_path
    )

    file_metadata = {
        "name": file_name
    }

    # --------------------------------------------------------
    # Put file inside selected folder
    # --------------------------------------------------------

    if folder_id:

        file_metadata["parents"] = [
            folder_id
        ]

    # --------------------------------------------------------
    # Detect MIME type
    # --------------------------------------------------------

    extension = os.path.splitext(
        file_path
    )[1].lower()

    mime_types = {

        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"

    }

    mime_type = mime_types.get(
        extension,
        "application/octet-stream"
    )

    media = MediaFileUpload(
        file_path,
        mimetype=mime_type,
        resumable=True
    )

    # --------------------------------------------------------
    # Upload
    # --------------------------------------------------------

    print(
        f"\nUploading: {file_name}"
    )

    existing_file = find_file_in_drive(
        service,
        os.path.basename(file_path),
        folder_id
    )

    if existing_file:
        print(
            f"File already exists in Google Drive: "
            f"{existing_file['name']}"
        )
        return existing_file

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name, webViewLink"
    ).execute()

    print(
        "Upload successful ✓"
    )

    print(
        f"File name : {uploaded_file.get('name')}"
    )

    print(
        f"File ID   : {uploaded_file.get('id')}"
    )

    print(
        f"Drive link: "
        f"{uploaded_file.get('webViewLink')}"
    )

    return uploaded_file