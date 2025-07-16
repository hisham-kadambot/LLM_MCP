import pytest
import requests
import base64
from unittest.mock import patch, MagicMock
from app.services.google_drive_service import GoogleDriveService

BASE_URL = "http://127.0.0.1:8001"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJyeWNhIiwiZXhwIjoxNzUyNjc1OTgwfQ.mB87YPw70r7Q7iLBdgAkVhhygk7mr7f8puQ8I_cikI8" 
HEADERS = {"Authorization": f"Bearer {JWT_TOKEN}"}

@pytest.mark.parametrize("message,expected_substring", [
    ("help", "Google Drive commands"),
    ("create folder test_pytest_folder", "Folder created"),
])
def test_llm_chat_tool_commands(message, expected_substring):
    response = requests.post(f"{BASE_URL}/chat", params={"message": message}, headers=HEADERS)
    assert response.status_code == 200
    assert expected_substring in response.text

def test_llm_chat_tool_upload_and_download(tmp_path):
    # Create a file to upload
    file_content = b"pytest file upload content"
    file_name = "pytest_upload.txt"
    file_path = tmp_path / file_name
    file_path.write_bytes(file_content)

    # Upload file
    upload_message = f"upload file {file_path}"
    response = requests.post(f"{BASE_URL}/chat", params={"message": upload_message}, headers=HEADERS)
    assert response.status_code == 200
    assert "File uploaded" in response.text

    # Extract file id from response (assumes id is in response)
    import re
    match = re.search(r"'id': '([^']+)'", response.text)
    file_id = match.group(1) if match else None
    assert file_id, "File ID not found in upload response"

    # Download file
    download_message = f"download file {file_id}"
    response = requests.post(f"{BASE_URL}/chat", params={"message": download_message}, headers=HEADERS)
    assert response.status_code == 200
    assert "File downloaded successfully" in response.text

# Improved unit tests for GoogleDriveService
@patch.object(GoogleDriveService, 'authenticate', return_value=True)
def test_upload_file_content(mock_auth):
    service = GoogleDriveService()
    service.authenticated = True
    service.service = MagicMock()
    mock_files = MagicMock()
    mock_create = MagicMock()
    mock_create.execute.return_value = {
        'id': 'testid', 'name': 'test.txt', 'size': 10, 'webViewLink': 'http://link', 'createdTime': 'now', 'modifiedTime': 'now'
    }
    mock_files.create.return_value = mock_create
    service.service.files.return_value = mock_files
    result = service.upload_file_content(b"abc", "test.txt")
    assert result['id'] == 'testid'
    assert result['name'] == 'test.txt'

@patch.object(GoogleDriveService, 'authenticate', return_value=True)
def test_download_file(mock_auth, tmp_path):
    service = GoogleDriveService()
    service.authenticated = True
    service.service = MagicMock()
    # Mock file metadata and download
    mock_files = MagicMock()
    mock_get = MagicMock()
    mock_get.execute.return_value = {'mimeType': 'application/octet-stream'}
    mock_get_media = MagicMock()
    mock_downloader = MagicMock()
    mock_downloader.next_chunk.side_effect = [(None, True)]
    with patch('app.services.google_drive_service.MediaIoBaseDownload', return_value=mock_downloader):
        mock_files.get.return_value = mock_get
        mock_files.get_media.return_value = mock_get_media
        service.service.files.return_value = mock_files
        # Patch open to write to a temp file
        file_id = 'testid'
        output_path = tmp_path / "downloaded_testid"
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = MagicMock()
            service.download_file(file_id, output_path=str(output_path))
        # No assertion needed, just ensure no exception 