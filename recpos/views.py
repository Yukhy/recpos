from __future__ import print_function
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from config.settings import SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE, BASE_DIR, REFRESH_TOKEN
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import base64
import re
import ast
import json


def gmail_get_service(user):
    #userのtokenを確認し、Gmail APIのserviceを返す
    creds = None
    token_file_path = BASE_DIR+'/recpos/gmail_tokens/'+user.email+'.json'
    user_profile = user.profile
    #userがtokenをもっていたらcredsに取り出す
    if user_profile.gmail_api_token!="":
        user_token = user_profile.gmail_api_token
        #api_tokenにrefresh_tokenが存在しない場合があるため追加
        if 'refresh_token' not in user_token:
            api_token = ast.literal_eval(user_token)
            api_token['refresh_token'] = REFRESH_TOKEN
            user_token = api_token
        #user.gmail_api_tokenからtoken.jasonを一時的に作成
            with open(token_file_path, 'w') as tmp_token:
                tmp_token.write(json.dumps(user_token))
        else :
            with open(token_file_path, 'w') as tmp_token:
                tmp_token.write(user_token)
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

def get_message_list(user_email, service):
        #受信ボックス内のメールを30件返す
        MessageList = []

        # メールIDの一覧を取得する(最大30件)
        messageIDlist = service.users().messages().list(userId=user_email, maxResults=30, labelIds="INBOX").execute()
        # 該当するメールが存在しない場合は、処理中断
        if messageIDlist["resultSizeEstimate"] == 0:
            return MessageList
        # メッセージIDを元に、メールの詳細情報を取得
        for message in messageIDlist["messages"]:
            row = {}
            row["ID"] = message["id"]
            MessageDetail = service.users().messages().get(userId=user_email, id=message["id"]).execute()

            if "UNREAD" in MessageDetail["labelIds"]:
                row["Unread"] = True
            else :
                row["Unread"] = False

            for header in MessageDetail["payload"]["headers"]:
                # 日付、送信元、件名を取得する
                if header["name"] == "Date":
                    row["Date"] = header["value"]
                elif header["name"] == "From":
                    row["From"] = header["value"]
                elif header["name"] == "To":
                    row["To"] = header["value"]
                elif header["name"] == "Subject":
                    row["Subject"] = header["value"]

            if 'data' in MessageDetail['payload']['body']:
                b64_message = MessageDetail['payload']['body']['data']
                row["Text"] = base64_decode(b64_message)
            elif MessageDetail["payload"]["parts"][0]["body"]["size"] == 0:
                if "snippet" in MessageDetail:
                    row["Text"] = MessageDetail["snippet"]
                else:
                    row["Text"] = "None Text"
            # Such as text/html
            elif MessageDetail['payload']['parts'] is not None:
                b64_message = MessageDetail['payload']['parts'][0]['body']['data']
                row["Text"] = base64_decode(b64_message)

            MessageList.append(row)
        return MessageList

def decode_date(date):
    #日付を読みやすい形に変換する
    month = ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    pattern = '([A-Z][a-z]{2}), (\d{1,2}) ([A-Z][a-z]{2}) (\d{4}) (\d{2}):(\d{2}):\d{2} \S*'
    content = re.match(pattern, date)
    result = "{0}/{1}/{2} {3} {4}:{5}"
    return result.format(content.group(4), month.index(content.group(3)), content.group(2), content.group(1), content.group(5), content.group(6))  

def base64_decode(b64_message):
    #textをデコードする
    message = base64.urlsafe_b64decode(
        b64_message + '=' * (-len(b64_message) % 4)).decode(encoding='utf-8')
    return message

def mark_as_read(user_email, service, id):
    #メールを既読にする
    query = {"removeLabelIds": ["UNREAD"]}
    service.users().messages().modify(userId=user_email, id=id, body=query).execute()
    return

def mark_as_unread(user_email, service, id):
    #メールを未読にする
    query = {"addLabelIds": ["UNREAD"]}
    service.users().messages().modify(userId=user_email, id=id, body=query).execute()
    return

@login_required
def index(request):
    return render(request, 'recpos/index.html')

@login_required
def mailbox(request):
    service = gmail_get_service(request.user)
    msg = get_message_list(request.user.email, service)
    data = {'messages': msg}
    return render(request, 'recpos/mailbox.html', data)

def login(request):
    return render(request, 'recpos/tmpLogin.html')

def privacy_policy(request):
    return render(request, 'recpos/privacy-policy.html')