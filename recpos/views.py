from __future__ import print_function
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from config.settings import SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE, BASE_DIR
from django.shortcuts import render
import re
from django.contrib.auth.decorators import login_required


def gmail_get_service(user):
    #userのtokenを確認し、Gmail APIのserviceを返す
    creds = None
    token_file_path = BASE_DIR+'/recpos/gmail_tokens/'+user.email+'.json'
    user_profile = user.profile
    #userがtokenをもっていたらcredsに取り出す
    if user_profile.gmail_api_token!="":
        #user.gmail_api_tokenからtoken.jasonを一時的に作成
        tmp_token = open(token_file_path, 'w')
        #json.dump(user.gmail_api_token,tmp_token,ensure_ascii=False)
        tmp_token.write(user_profile.gmail_api_token)
        tmp_token.close()
        creds = Credentials.from_authorized_user_file(token_file_path, SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE)
    #tokenの有効期限が切れていたらリフレッシュ、なかったら作成し、userに格納する
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(BASE_DIR+'/recpos/credentials.json', SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE)
            creds = flow.run_local_server(port=8080)
        with open(token_file_path, 'w') as token:
            token.write(creds.to_json())
    user_profile.gmail_api_token = creds.to_json()
    user_profile.save()
    service = build('gmail', 'v1', credentials=creds)
    return service

def get_message_list(service):

        MessageList = []

        # メールIDの一覧を取得する(最大30件)
        messageIDlist = service.users().messages().list(userId="me", maxResults=30, labelIds="INBOX").execute()
        # 該当するメールが存在しない場合は、処理中断
        if messageIDlist["resultSizeEstimate"] == 0:
            return MessageList
        # メッセージIDを元に、メールの詳細情報を取得
        for message in messageIDlist["messages"]:
            row = {}
            row["ID"] = message["id"]
            MessageDetail = service.users().messages().get(userId="me", id=message["id"]).execute()

            if "UNREAD" in MessageDetail["labelIds"]:
                row["Unread"] = True
            else :
                row["Unread"] = False

            for header in MessageDetail["payload"]["headers"]:
                # 日付、送信元、件名を取得する
                if header["name"] == "Date":
                    row["Date"] = encode_date(header["value"])
                elif header["name"] == "From":
                    row["From"] = header["value"]
                elif header["name"] == "To":
                    row["To"] = header["value"]
                elif header["name"] == "Subject":
                    row["Subject"] = header["value"]
            MessageList.append(row)

        return MessageList

def encode_date(date):
    month = ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    pattern = '([A-Z][a-z]{2}), (\d{1,2}) ([A-Z][a-z]{2}) (\d{4}) (\d{2}):(\d{2}):\d{2} \S*'
    content = re.match(pattern, date)
    result = "{0}/{1}/{2} {3} {4}:{5}"
    return result.format(content.group(4), month.index(content.group(3)), content.group(2), content.group(1), content.group(5), content.group(6))  

@login_required
def index(request):
    return render(request, 'recpos/index.html')

def mailbox(request):
    service = gmail_get_service(request.user)
    msg = get_message_list(service)
    data = {'messages': msg}
    return render(request, 'recpos/mailbox.html', data)

def login(request):
    return render(request, 'recpos/tmpLogin.html')