from __future__ import print_function
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from config.settings import SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE, BASE_DIR
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def gmail_get_service(user):
    #userのtokenを確認し、Gmail APIのserviceを返す
    creds = None
    token_file_path = BASE_DIR+'/recpos/gmail_tokens/'+user.email+'.json'
    #userがtokenをもっていたらcredsに取り出す
    if user.gmail_api_token!="":
        #user.gmail_api_tokenからtoken.jasonを一時的に作成
        tmp_token = open(token_file_path, 'w')
        #json.dump(user.gmail_api_token,tmp_token,ensure_ascii=False)
        tmp_token.write(user.gmail_api_token)
        tmp_token.close()
        creds = Credentials.from_authorized_user_file(token_file_path, SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE)
    #tokenの有効期限が切れていたらリフレッシュ、なかったら作成し、userに格納する
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(BASE_DIR+'/recpos/credentials.json', SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE)
            creds = flow.run_local_server(port=0)
        with open(token_file_path, 'w') as token:
            token.write(creds.to_json())
    user.gmail_api_token = creds.to_json()
    user.save()
    service = build('gmail', 'v1', credentials=creds)
    return service

def gmail_get_messages(service):
    # メッセージの一覧を取得
    messages = service.users().messages()
    msg_list = messages.list(userId='me', maxResults=10).execute()

    # 取得したメッセージの一覧を表示
    for msg in msg_list['messages']:
        topid = msg['id']
        msg = messages.get(userId='me', id=topid).execute()
    return msg

@login_required
def index(request):
    return render(request, 'recpos/index.html')

def mailbox(request):

    service = gmail_get_service(request.user)
    msg = gmail_get_messages(service)
    return render(request, 'recpos/mailbox.html')
