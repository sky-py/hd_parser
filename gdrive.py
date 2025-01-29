from pathlib import Path
from constants import GLOBAL_MAX_TRIES, GOOGLE_CREDENTIALS
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from loguru import logger
from retry import retry

SCOPES = ['https://www.googleapis.com/auth/drive']


@retry(max_tries=GLOBAL_MAX_TRIES)
def upload_file_as_document(file: Path) -> str:
    cred = Credentials.from_service_account_file(str(GOOGLE_CREDENTIALS), scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=cred)

    file_metadata = {'name': file.stem, 'mimeType': 'application/vnd.google-apps.document'}
    media = MediaFileUpload(filename=str(file), mimetype='text/html')
    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = uploaded_file.get('id')
    logger.info(f'Got file ID: {file_id} for file: {file}')

    permission = {'type': 'anyone', 'role': 'writer'}
    drive_service.permissions().create(fileId=file_id, body=permission).execute()
    link = f'https://docs.google.com/document/d/{file_id}'
    logger.info(f'Permission changed. Document link: {link} for file: {file}')
    return link


if __name__ == '__main__':
    print(
        upload_file_as_document(
            Path(r'd:\user\Dropbox\Python\parser_hd_server\out\Союз Аліна Ісакова и Чоловік Аліни_ua.html')
        )
    )
