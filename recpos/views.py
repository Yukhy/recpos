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
from django.contrib.auth.models import User
from django.shortcuts import redirect
from .forms import UserChangeForm, ProfileChangeForm
import sys


class Message:
    id = None
    unread = None
    labels = None
    subject = None
    text = None
    date = None
    from_address = None
    to_address = None

    def __init__(self, id:str, labels:list, subject:str, text:str, date:str, from_address:str, to_address:str):
        self.id = id
        self.labels = labels
        self.subject = subject
        self.text = text
        self.date = date
        self.from_address = from_address
        self.to_address = to_address

    def to_dict(self):
        message = {}
        message['id'] = self.id
        message['labels'] = self.labels
        message['subject'] = self.subject
        message['text'] = self.text
        message['date'] = self.date
        message['from_address'] = self.from_address
        message['to_address'] = self.to_address
        return message

#userのtokenを確認し、Gmail APIのserviceを返す
def gmail_get_service(user):
    creds = None
    token_file_path = BASE_DIR+'/recpos/gmail_tokens/'+user.email+'.json'
    user_profile = user.profile
    #userがtokenをもっていたらcredsに取り出す
    if user_profile.gmail_api_token!='':
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

#削除予定
#受信ボックス内のメールを30件返す
""" def get_message_list(user_email, service):
    #受信ボックス内のメールを30件返す
    MessageList = []

    # メールIDの一覧を取得する(最大30件)
    messageIDlist = service.users().messages().list(userId=user_email, maxResults=30, labelIds='INBOX').execute()
    # 該当するメールが存在しない場合は、処理中断
    if messageIDlist['resultSizeEstimate'] == 0:
        return MessageList
    # メッセージIDを元に、メールの詳細情報を取得
    for message in messageIDlist['messages']:
        row = {}
        row['ID'] = message['id']
        MessageDetail = service.users().messages().get(userId=user_email, id=message['id']).execute()

        if 'UNREAD' in MessageDetail['labelIds']:
            row['Unread'] = True
        else :
            row['Unread'] = False

        for header in MessageDetail['payload']['headers']:
            # 日付、送信元、件名を取得する
            if header['name'] == 'Date':
                row['Date'] = header['value']
            elif header['name'] == 'From':
                row['From'] = header['value']
            elif header['name'] == 'To':
                row['To'] = header['value']
            elif header['name'] == 'Subject':
                row['Subject'] = header['value']

        if 'data' in MessageDetail['payload']['body']:
            b64_message = MessageDetail['payload']['body']['data']
            row['Text'] = base64_decode(b64_message)
        elif MessageDetail['payload']['parts'][0]['body']['size'] == 0:
            if 'snippet' in MessageDetail:
                row['Text'] = MessageDetail['snippet']
            else:
                row['Text'] = 'None Text'
        # Such as text/html
        elif MessageDetail['payload']['parts'] is not None:
            b64_message = MessageDetail['payload']['parts'][0]['body']['data']
            row['Text'] = base64_decode(b64_message)

        MessageList.append(row)
    return MessageList """

#条件に合うメッセージのidをリストで返す
def get_message_id(user_email, service, num, label, query=''):
    messageIDlist = service.users().messages().list(userId=user_email, maxResults=num, labelIds=label, q=query).execute()
    idlist = []
    if 'messages' not in messageIDlist:
        return idlist
    for message in messageIDlist['messages']:
        idlist.append(message['id'])
    return idlist

#メッセージを取得して、Messageに格納して返す
def get_message_content(user_email, service, id):
    MessageDetail = service.users().messages().get(userId=user_email, id=id).execute()

    labels = None
    subject = None
    text = None
    date = None
    from_address = None
    to_address = None

    labels = MessageDetail['labelIds']

    for header in MessageDetail['payload']['headers']:
        # 日付、送信元、件名を取得する
        if header['name'] == 'Date':
            date = header['value']
        elif header['name'] == 'From':
            from_address = header['value']
        elif header['name'] == 'To':
            to_address = header['value']
        elif header['name'] == 'Subject':
            subject = header['value']

    if 'data' in MessageDetail['payload']['body']:
        b64_message = MessageDetail['payload']['body']['data']
        text = base64_decode(b64_message)
    elif MessageDetail['payload']['parts'][0]['body']['size'] == 0:
        if 'snippet' in MessageDetail:
            text = MessageDetail['snippet']
        else:
            text = 'None Text'
    # Such as text/html
    elif MessageDetail['payload']['parts'] is not None:
        b64_message = MessageDetail['payload']['parts'][0]['body']['data']
        text = base64_decode(b64_message)

    return Message(id, labels, subject, text, date, from_address, to_address)

#HistoryのリストとHistoryIdを返す
def get_history_list(user_email, service, historyid, label=None, history_type=None):
    historylist = []
    pagetoken=None
    while True:
        history = service.users().history().list(userId=user_email, maxResults=50, pageToken=pagetoken, startHistoryId=historyid, labelId=label).execute()
        if 'history' not in history:
            break
        historylist += history['history']
        if 'nextPageToken' not in history:
            break
        pegetoken = history['nextPageToken']
    historyid = history['historyId']
    return historylist, historyid

#Historyからmessagesを更新する
def change_by_history(user_email, service, messages, history_list):
    #messagesはlistで渡す
    for history in history_list:
        if 'messagesAdded' in history:
            for message in history['messagesAdded']:
                id = message['message']['id']
                msg = get_message_content(user_email, service, id)
                messages.insert(0, msg.to_dict())
        if 'messagesDeleted' in history:
            for message in history['messagesDeleted']:
                id = message['message']['id']
                index = get_message_index(messages, id)
                messages.pop(index)
        if 'labelsAdded' in history:
            for message in history['labelsAdded']:
                id = message['message']['id']
                msg = get_message_content(user_email, service, id)
                index = get_message_index(messages, id)
                messages[index] = msg.to_dict()
        if 'labelsRemoved' in history:
            for message in history['labelsRemoved']:
                id = message['message']['id']
                msg = get_message_content(user_email, service, id)
                index = get_message_index(messages, id)
                messages[index] = msg.to_dict()
    return messages

#user.profile.messages['message']からidを検索し添字を返す
def get_message_index(messages, id):
    #messagesはlistで渡す
    for index in range(len(messages)):
        if messages[index]['id'] == id:
            break
    return index

#日付を読みやすい形に変換する
def decode_date(date):
    month = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    pattern = '([A-Z][a-z]{2}), (\d{1,2}) ([A-Z][a-z]{2}) (\d{4}) (\d{2}):(\d{2}):\d{2} \S*'
    content = re.match(pattern, date)
    result = '{0}/{1}/{2} {3} {4}:{5}'
    return result.format(content.group(4), month.index(content.group(3)), content.group(2), content.group(1), content.group(5), content.group(6))  

#textをデコードする
def base64_decode(b64_message):
    message = base64.urlsafe_b64decode(
        b64_message + '=' * (-len(b64_message) % 4)).decode(encoding='utf-8')
    return message

#メールを既読にする
def mark_as_read(user_email, service, id):
    query = {'removeLabelIds': ['UNREAD']}
    service.users().messages().modify(userId=user_email, id=id, body=query).execute()
    return

#メールを未読にする
def mark_as_unread(user_email, service, id):
    query = {'addLabelIds': ['UNREAD']}
    service.users().messages().modify(userId=user_email, id=id, body=query).execute()
    return

@login_required
def index(request):
    user = request.user
    service = gmail_get_service(user)
    profile = user.profile
    user_email = user.email
    user_messages = json.loads(profile.messages)['messages']
    last_history_id = profile.last_history_id
    history_list, history_id = get_history_list(user_email, service, last_history_id)
    if history_list != []:
        user_messages = change_by_history(user_email, service, user_messages, history_list)
        profile.messages = json.dumps({'messages':user_messages})
    profile.last_history_id = history_id
    profile.save()

    params = {'userform':UserChangeForm(instance=user), 'profileform':ProfileChangeForm(instance=user.profile)}
    if request.method == 'POST':
        form1 = UserChangeForm(request.POST, instance=user)
        form2 = ProfileChangeForm(request.POST, instance=user.profile)
        if form1.is_valid() and form2.is_valid():
            form1.save()
            form2.save()
            return redirect('recpos:index')
    
    return render(request, 'recpos/index.html', params)

@login_required
def mailbox(request, num):
    user_messages = json.loads(request.user.profile.messages)
    messages = []
    num_msg = len(user_messages['messages'])
    for i in range(30*(num-1),30*(num)):
        if i >= num_msg:
            break
        messages.append(user_messages['messages'][i])
    data = {'messages': messages}
    return render(request, 'recpos/mailbox.html', data)

def privacy_policy(request):
    return render(request, 'recpos/privacy-policy.html')
    
def login(request):
    user = request.user
    user_messages = json.loads(user.profile.messages)
    if user_messages['messages'] == []:
        service = gmail_get_service(user)
        idlist = get_message_id(user.email, service, 100, 'INBOX')
        messages = []
        for id in idlist:
            if (sys.getsizeof(messages) >= 5242880):
                break
            message = get_message_content(user.email, service, id)
            messages.append(message.to_dict())
        user_messages = {'messages':messages}
        user.profile.messages = json.dumps(user_messages)
        user.profile.last_history_id = service.users().getProfile(userId=user.email).execute()['historyId']
        user.profile.save()
    return render(request, 'recpos/index.html')
