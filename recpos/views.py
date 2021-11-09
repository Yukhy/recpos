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

MESSAGE_NUM = 20
DEFAULT_SAVE_MESSAGE_NUM = 100


class Message:
    index = None
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

class Label:
    id = None
    name = None
    type = None
    
    def __init__(self, id:str, name:str, type:str):
        self.id = id
        self.name = name
        self.type = type
        
    def to_dict(self):
        label = {}
        label['id'] = self.id
        label['name'] = self.name
        label['type'] = self.type
        return label


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
        #user.gmail_api_tokenからtoken.jasonを一時的に作成
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

#labelのリストを取得する
def get_labels(user_email, service):
    labels = service.users().labels().list(userId=user_email).execute().get('labels', [])
    user_labels = []
    for label in labels:
        if 'labelListVisibility'in label and label['labelListVisibility']=='labelHide':
            continue
        id = label['id']
        name = label['name']
        type = label['type']
        user_labels.append(Label(id, name, type).to_dict())
    return user_labels

#条件に合うメッセージのidをリストで返す
def get_message_id(user_email, service, num, label=None, query=None):
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

    if 'labelIds' in MessageDetail:
        labels = MessageDetail['labelIds']
    else:
        labels = []

    for header in MessageDetail['payload']['headers']:
        # 日付、送信元、件名を取得する
        if header['name'] == 'Date':
            date = decode_date(header['value'])
        elif header['name'] == 'From':
            from_address = decode_address(header['value'])
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

#alias宛のメールを取得する
def get_alias_message(user_alias, messages, num, pagenum, label):
    #messageはlistで渡す
    #numは1ページに表示する件数
    alias_messages = []
    for message in messages:
        if len(alias_messages) > num * pagenum:
            break
        if message['to_address'] == user_alias and label in message['labels']:
            alias_messages.append(message)
    return alias_messages

#messageをラベルでフィルタリングする
def filter_label_message(messages, labels, num, pagenum):
    #messageはlistで渡す
    #numは1ページに表示する件数
    alias_messages = []
    for message in messages:
        if len(alias_messages) > num * pagenum:
            break
        if labels in message['labels']:
            alias_messages.append(message)
    return alias_messages

#user.profile.messages['message']からidを検索し添字を返す
def get_message_index(messages, id):
    #messagesはlistで渡す
    for index in range(len(messages)):
        if messages[index]['id'] == id:
            break
    return index

#日付を読みやすい形に変換する
def decode_date(date):
    result = {}
    month = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    result['year'] = int(re.search('\d{4}', date).group())
    result['month'] = month.index(re.search('Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec', date).group())
    result['date'] = int(re.search('\d{1,2}', date).group())
    time = re.search('(\d{1,2}):(\d{1,2}):\d{1,2}', date)
    result['hour'] = time.group(1)
    result['minute'] = time.group(2)
    return result

#送り主を読みやすい形に変換する
def decode_address(address):
    result = re.search('"?(.*?)"?\s<(.*?)>',address)
    from_address = {
        'address': result.group(1),
        'name': result.group(2),
    }
    return from_address

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
    params = {
        'userform': UserChangeForm(instance=user),
        'profileform': ProfileChangeForm(instance=user.profile),
        'labels': json.loads(user.profile.labels),
        }
    if request.method == 'POST':
        form1 = UserChangeForm(request.POST, instance=user)
        form2 = ProfileChangeForm(request.POST, instance=user.profile)
        if form1.is_valid() and form2.is_valid():
            form1.save()
            form2.save()
            return redirect('recpos:index')
    
    return render(request, 'recpos/index.html', params)

@login_required
def mailbox(request, label='INBOX', page=1):
    #messageの更新
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
    
    #messageからMESSAGE_NUM件を表示する
    inbox_message = filter_label_message(user_messages, label, MESSAGE_NUM, page)
    messages = []
    num_msg = len(inbox_message)
    for i in range(MESSAGE_NUM*(page-1),MESSAGE_NUM*(page)):
        if i >= num_msg:
            break
        inbox_message[i]['index'] = i
        messages.append(inbox_message[i])

    labels = json.loads(profile.labels)
    label_name = label
    for l in labels:
        if l['id'] == label:
            label_name = l['name']

    data = {
        'messages': messages,
        'labels': labels,
        'label': {'id': label, 'name': label_name},
        'page': {'now': str(page), 'prev': page-1, 'next': page+1},
        }
    return render(request, 'recpos/mailbox.html', data)

@login_required
def alias(request, label='INBOX', page=1):
    user = request.user
    service = gmail_get_service(user)
    profile = user.profile
    user_email = user.email
    user_alias = profile.alias

    #messageの更新
    user_messages = json.loads(profile.messages)['messages']
    last_history_id = profile.last_history_id
    history_list, history_id = get_history_list(user_email, service, last_history_id)
    if history_list != []:
        user_messages = change_by_history(user_email, service, user_messages, history_list)
        profile.messages = json.dumps({'messages':user_messages})
    profile.last_history_id = history_id
    profile.save()

    if user_alias == '':
        return redirect('recpos:mailbox')

    #alias宛のmessageをMESSAGE_NUM件表示する
    alias_message = get_alias_message(user_alias,user_messages, MESSAGE_NUM, page, label)
    messages = []
    num_msg = len(alias_message)
    for i in range(MESSAGE_NUM*(page-1),MESSAGE_NUM*(page)):
        if i >= num_msg:
            break
        alias_message[i]['index'] = i
        messages.append(alias_message[i])

    labels = json.loads(profile.labels)
    label_name = label
    for l in labels:
        if l['id'] == label:
            label_name = l['name']

    data = {
        'messages': messages,
        'labels': labels,
        'label': {'id': label, 'name': label_name},
        'page': {'now': str(page), 'prev': page-1, 'next': page+1},
        }
    return render(request, 'recpos/mailbox.html', data)

def privacy_policy(request):
    return render(request, 'recpos/privacy-policy.html')
    
def login(request):
    user = request.user
    user_messages = json.loads(user.profile.messages)
    service = gmail_get_service(user)
    if user_messages['messages'] == []:
        idlist = get_message_id(user.email, service, DEFAULT_SAVE_MESSAGE_NUM)
        messages = []
        for id in idlist:
            if (sys.getsizeof(messages) >= 5242880):
                break
            message = get_message_content(user.email, service, id)
            messages.append(message.to_dict())
        user_messages = {'messages':messages}
        user.profile.messages = json.dumps(user_messages)
        user.profile.last_history_id = service.users().getProfile(userId=user.email).execute()['historyId']
    user.profile.labels = json.dumps(get_labels(user.email, service))
    user.profile.save()
    return redirect('recpos:index')

def mail_detail(request):
    return render(request, 'recpos/mail-detail.html')