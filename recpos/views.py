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
from .forms import ProfileChangeForm, RegisterEventForm, AddTaskForm
import sys
import datetime

MESSAGE_NUM = 20
DEFAULT_SAVE_MESSAGE_NUM = 10
DOMEIN = "http://localhost:8000/"

EVENT_AND_TASK_PARAMS = {'eventform': RegisterEventForm(), 'taskform': AddTaskForm()}


class Message:
    index = None
    url = None
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


# userのtokenを確認し、Gmail APIのserviceを返す
def gmail_get_service(user):
    creds = None
    token_file_path = BASE_DIR+'/recpos/gmail_tokens/'+user.email+'.json'
    user_profile = user.profile
    # userがtokenをもっていたらcredsに取り出す
    if user_profile.gmail_api_token!='':
        user_token = user_profile.gmail_api_token
        # api_tokenにrefresh_tokenが存在しない場合があるため追加
        if 'refresh_token' not in user_token:
            api_token = ast.literal_eval(user_token)
            api_token['refresh_token'] = REFRESH_TOKEN
            user_token = api_token
        # user.gmail_api_tokenからtoken.jasonを一時的に作成
            with open(token_file_path, 'w') as tmp_token:
                tmp_token.write(json.dumps(user_token))
        else :
            with open(token_file_path, 'w') as tmp_token:
                tmp_token.write(user_token)
        creds = Credentials.from_authorized_user_file(token_file_path, SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE)
    # tokenの有効期限が切れていたらリフレッシュ、なかったら作成し、userに格納する
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

# labelのリストを取得する
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

# 条件に合うメッセージのidをリストで返す
def get_message_id(user_email, service, num, label=None, query=None):
    messageIDlist = service.users().messages().list(userId=user_email, maxResults=num, labelIds=label, q=query).execute()
    idlist = []
    if 'messages' not in messageIDlist:
        return idlist
    for message in messageIDlist['messages']:
        idlist.append(message['id'])
    return idlist

# メッセージを取得して、Messageに格納して返す
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
        if header['name'] == 'Date' or header['name'] == 'date':
            date = decode_date(header['value'])
        elif header['name'] == 'From' or header['name'] == 'from':
            from_address = decode_from_address(header['value'])
        elif header['name'] == 'To' or header['name'] == 'to':
            to_address = header['value']
        elif header['name'] == 'Subject' or header['name'] == 'subject':
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

# HistoryのリストとHistoryIdを返す
def get_history_list(user_email, service, historyid, label=None, history_type=None):
    historylist = []
    pagetoken=None
    while True:
        history = service.users().history().list(userId=user_email, maxResults=500, pageToken=pagetoken, startHistoryId=historyid, labelId=label, historyTypes = history_type).execute()
        historyid = history['historyId']
        if 'history' not in history:
            break
        historylist += history['history']
        if 'nextPageToken' not in history:
            break
        pegetoken = history['nextPageToken']
    return historylist, historyid

# Historyからmessagesを更新する
def change_by_history(user_email, service, messages, history_list):
    # messagesはlistで渡す
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

# alias宛のメールを取得する
def get_alias_message(user_alias, messages, num, pagenum, label):
    # messageはlistで渡す
    # numは1ページに表示する件数
    alias_messages = []
    index_list = []
    for index, message in enumerate(messages):
        if len(alias_messages) > num * pagenum:
            break
        if message['to_address'] == user_alias and label in message['labels']:
            alias_messages.append(message)
            index_list.append(index)
    return alias_messages, index_list

# messageをラベルでフィルタリングする
def filter_label_message(messages, labels, num, pagenum):
    # messageはlistで渡す
    # numは1ページに表示する件数
    filter_messages = []
    index_list = []
    for index, message in enumerate(messages):
        if len(filter_messages) > num * pagenum:
            break
        if labels in message['labels']:
            filter_messages.append(message)
            index_list.append(index)
    return filter_messages, index_list

# user.profile.messages['message']からidを検索し添字を返す
def get_message_index(messages, id):
    # messagesはlistで渡す
    for index in range(len(messages)):
        if messages[index]['id'] == id:
            break
    return index

#日付を読みやすい形に変換する
def decode_date(receive_time):
    month_list = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    year = int(re.search('\d{4}', receive_time).group())
    month = month_list.index(re.search('Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec', receive_time).group())
    date = int(re.search('\d{1,2}', receive_time).group())
    time = re.search('(\d{1,2}):(\d{1,2}):(\d{1,2})', receive_time)
    hour = int(time.group(1))
    minute = int(time.group(2))
    second = int(time.group(3))
    rec_time = datetime.datetime(year, month, date, hour, minute, second)
    time_dif = re.search('([-|+])(\d\d)00',receive_time)
    if time_dif:
        if time_dif.group(1) == '+':
            hour_dif = 9-int(time_dif.group(2))
        elif time_dif.group(1) == '-' :
            hour_dif = 9+int(time_dif.group(2))
        rec_time = rec_time + datetime.timedelta(hours=hour_dif)
    year = rec_time.year
    month = rec_time.month
    date = rec_time.day
    hour = rec_time.hour
    if rec_time.minute < 10:
        minute = '0' + str(rec_time.minute)
    else:
        minute = rec_time.minute
    return {'year':year, 'month':month, 'date':date, 'hour':hour, 'minute':minute}

# 送り主を読みやすい形に変換する
def decode_from_address(from_address):
    address_result = re.match(('"?(.*?)"? <(.*)@(.*)>'), from_address)
    if address_result:
        name = address_result.group(1)
        address = address_result.group(2) + "@" + address_result.group(3)
    else:
        address_result = re.search('<?(.*)@(.*)>?', from_address)
        name = address_result.group(1)
        address = address_result.group(1) + "@" + address_result.group(2)
    return {'name': name, 'from_address': address}

# textをデコードする
def base64_decode(b64_message):
    message = base64.urlsafe_b64decode(
        b64_message + '=' * (-len(b64_message) % 4)).decode(encoding='utf-8')
    return message

# メールを既読にする
def mark_as_read(user_email, service, id):
    query = {'removeLabelIds': ['UNREAD']}
    service.users().messages().modify(userId=user_email, id=id, body=query).execute()
    return

# メールを未読にする
def mark_as_unread(user_email, service, id):
    query = {'addLabelIds': ['UNREAD']}
    service.users().messages().modify(userId=user_email, id=id, body=query).execute()
    return

# メールにスターをつける
def mark_as_star(user_email, service, id):
    query = {'addLabelIds': ['STARRED']}
    service.users().messages().modify(userId=user_email, id=id, body=query).execute()
    return

# メールのスターを外す
def mark_as_unstar(user_email, service, id):
    query = {'removeLabelIds': ['STARRED']}
    service.users().messages().modify(userId=user_email, id=id, body=query).execute()
    return

# メールをTRASHに移動する
def move_to_trash(user_email, service, id, labels):
    query = {'addLabelIds': ['TRASH'], 'removeLabelIds': labels}
    service.users().messages().modify(userId=user_email, id=id, body=query).execute()
    return

# メールをTRASHから戻す
def put_back_message(user_email, service, id):
    query = {'addLabelIds': ['INBOX'], 'removeLabelIds': ['TRASH']}
    service.users().messages().modify(userId=user_email, id=id, body=query).execute()
    return

# 略称されたURLをデコードする
def decode_url(user_labels, omiturl):
    # <aliasの有無:A><labelの引数(user_labelの引数):l><page:p>
    url = "mailbox/"
    alias = re.match('A.*',omiturl)
    if alias:
        url = "alias/" + url
    labelpage = re.search("A?l([\d+]|TRASH)p(\d+)",omiturl)
    if labelpage.group(1) == 'TRASH':
        url += 'TRASH' + '/' + str(labelpage.group(2)) + '/'
    else:
        url += user_labels[int(labelpage.group(1))]['name'] + '/' + str(labelpage.group(2)) + '/'
    return url

@login_required
def index(request):
    user = request.user
    params = {
        'profileform': ProfileChangeForm(instance=user.profile),
        'labels': json.loads(user.profile.labels),
        }
    params.update(EVENT_AND_TASK_PARAMS)
    if request.method == 'POST':
        form2 = ProfileChangeForm(request.POST, instance=user.profile)
        if form2.is_valid():
            form2.save()
            return redirect('recpos:index')
    
    return render(request, 'recpos/index.html', params)

@login_required
def mailbox(request, label='INBOX', page=1):
    user = request.user
    service = gmail_get_service(user)
    profile = user.profile
    user_email = user.email
    user_messages = json.loads(profile.messages)['messages']

    if request.method == 'POST':
        proc = request.POST.get('type')
        indexes = request.POST.getlist('index', None)
        if proc == 'star':
            for index in indexes:
                print("kita")
                message = user_messages[int(index)]
                mark_as_star(user_email, service, message['id'])
                if 'STARRED' not in message['labels']:
                    message['labels'].append('STARRED')
                    user_messages[int(index)] = message
        elif proc == 'trash':
            for index in indexes:
                message = user_messages[int(index)]
                move_to_trash(user.email, service, message['id'], message['labels'])
                if 'TRASH' not in message['labels']:
                    message['labels'] = ['TRASH']
                    user_messages[int(index)] = message
        user.profile.messages = json.dumps({'messages':user_messages})
        user.profile.save()

    # messageの更新
    last_history_id = profile.last_history_id
    history_list, history_id = get_history_list(user_email, service, last_history_id)
    if history_list != []:
        user_messages = change_by_history(user_email, service, user_messages, history_list)
        profile.messages = json.dumps({'messages':user_messages})
    profile.last_history_id = history_id
    profile.save()

    labels = json.loads(profile.labels)
    label_name = label
    label_index = label
    for l in labels:
        if l['id'] == label:
            label_name = l['name']
            label_index = labels.index(l)
    
    # messageからMESSAGE_NUM件を表示する
    inbox_message, index_list = filter_label_message(user_messages, label, MESSAGE_NUM, page)
    messages = []
    num_msg = len(inbox_message)
    for i in range(MESSAGE_NUM*(page-1),MESSAGE_NUM*(page)):
        if i >= num_msg:
            break
        inbox_message[i]['index'] = index_list[i]
        # detailページから戻ってくるために、前のURLを省略してmessageに保存する
        # 省略されたURLはdetailのURLの後ろにつける
        # <aliasの有無:A><labelの引数(user_labelの引数):l><page:p>
        inbox_message[i]['url'] = "l" + str(label_index) + "p" + str(page)
        messages.append(inbox_message[i])

    data = {
        'messages': messages,
        'labels': labels,
        'alias': False,
        'label': {'id': label, 'name': label_name},
        'page': {'now': str(page), 'prev': page-1, 'next': page+1},
        }
    data.update(EVENT_AND_TASK_PARAMS)
    return render(request, 'recpos/mailbox.html', data)

@login_required
def alias(request, label='INBOX', page=1):
    user = request.user
    service = gmail_get_service(user)
    profile = user.profile
    user_email = user.email
    user_alias = profile.alias
    user_messages = json.loads(profile.messages)['messages']

    if request.method == 'POST':
        proc = request.POST.get('type')
        indexes = request.POST.getlist('index', None)
        if proc == 'star':
            for index in indexes:
                print("kita")
                message = user_messages[int(index)]
                mark_as_star(user_email, service, message['id'])
                if 'STARRED' not in message['labels']:
                    message['labels'].append('STARRED')
                    user_messages[int(index)] = message
        elif proc == 'trash':
            for index in indexes:
                message = user_messages[int(index)]
                move_to_trash(user.email, service, message['id'], message['labels'])
                if 'TRASH' not in message['labels']:
                    message['labels'] = ['TRASH']
                    user_messages[int(index)] = message
        user.profile.messages = json.dumps({'messages':user_messages})
        user.profile.save()

    # messageの更新
    last_history_id = profile.last_history_id
    history_list, history_id = get_history_list(user_email, service, last_history_id)
    if history_list != []:
        user_messages = change_by_history(user_email, service, user_messages, history_list)
        profile.messages = json.dumps({'messages':user_messages})
    profile.last_history_id = history_id
    profile.save()

    if user_alias == '':
        return redirect('recpos:mailbox')

    labels = json.loads(profile.labels)
    label_name = label
    for l in labels:
        if l['id'] == label:
            label_name = l['name']
            label_index = labels.index(l)

    # alias宛のmessageをMESSAGE_NUM件表示する
    alias_message, index_list = get_alias_message(user_alias,user_messages, MESSAGE_NUM, page, label)
    messages = []
    num_msg = len(alias_message)
    for i in range(MESSAGE_NUM*(page-1),MESSAGE_NUM*(page)):
        if i >= num_msg:
            break
        alias_message[i]['index'] = index_list[i]
        # detailページから戻ってくるために、前のURLを省略してmessageに保存する
        # 省略されたURLはdetailのURLの後ろにつける
        # <aliasの有無:A><labelの引数(user_labelの引数):l><page:p>
        alias_message[i]['url'] = "A" + "l" + str(label_index) + "p" + str(page)
        messages.append(alias_message[i])

    data = {
        'messages': messages,
        'labels': labels,
        'alias': True,
        'label': {'id': label, 'name': label_name},
        'page': {'now': str(page), 'prev': page-1, 'next': page+1},
        }
    data.update(EVENT_AND_TASK_PARAMS)
    return render(request, 'recpos/mailbox.html', data)

@login_required
def mail_detail(request, index, prev):
    # detailページから戻ってくるために、前のURLを省略してmessageに保存する(views.mailbox,vews.aliasで行う)
    user_messages = json.loads(request.user.profile.messages)['messages']
    message = user_messages[index]
    user_labels = json.loads(request.user.profile.labels)
    if 'UNREAD' in message['labels']:
        service = gmail_get_service(request.user)
        mark_as_read(request.user.email, service, message['id'])
    data = {
        'message': user_messages[index],
        'index': index,
        'prev': prev,
        # 前のページに戻るためのURL
        'url': DOMEIN + decode_url(user_labels, prev),
    }
    data.update(EVENT_AND_TASK_PARAMS)
    return render(request, 'recpos/mail-detail.html', data)

def star(request, index, prev):
    user = request.user
    service = gmail_get_service(user)
    user_messages = json.loads(user.profile.messages)['messages']
    message = user_messages[index]
    mark_as_star(user.email, service, message['id'])
    if 'STARRED' not in message['labels']:
        message['labels'].append('STARRED')
        user_messages[index] = message
        user.profile.messages = json.dumps({'messages':user_messages})
        user.profile.save()
    return redirect(DOMEIN + 'mailbox/detail/' + str(index) + '/' + prev + '/')

def unstar(request, index, prev):
    user = request.user
    service = gmail_get_service(user)
    user_messages = json.loads(user.profile.messages)['messages']
    message = user_messages[index]
    mark_as_unstar(user.email, service, message['id'])
    if 'STARRED' in message['labels']:
        message['labels'].remove('STARRED')
        user_messages[index] = message
        user.profile.messages = json.dumps({'messages':user_messages})
        user.profile.save()
    return redirect(DOMEIN + 'mailbox/detail/' + str(index) + '/' + prev + '/')

def trash(request, index, prev):
    user = request.user
    service = gmail_get_service(user)
    user_messages = json.loads(user.profile.messages)['messages']
    message = user_messages[index]
    move_to_trash(user.email, service, message['id'], message['labels'])
    if 'TRASH' not in message['labels']:
        message['labels'] = ['TRASH']
        user_messages[index] = message
        user.profile.messages = json.dumps({'messages':user_messages})
        user.profile.save()
    return redirect(DOMEIN + 'mailbox/detail/' + str(index) + '/' + prev + '/')

def putback(request, index, prev):
    user = request.user
    service = gmail_get_service(user)
    user_messages = json.loads(user.profile.messages)['messages']
    message = user_messages[index]
    put_back_message(user.email, service, message['id'])
    if 'TRASH' in message['labels']:
        message['labels'] = ['INBOX']
        user_messages[index] = message
        user.profile.messages = json.dumps({'messages':user_messages})
        user.profile.save()
    return redirect(DOMEIN + 'mailbox/detail/' + str(index) + '/' + prev + '/')

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

def opensource(request):
    return render(request, 'recpos/opensource.html')

def company_list(request):
    return render(request, 'recpos/company-list.html', EVENT_AND_TASK_PARAMS)

def my_task(request):
    return render(request, 'recpos/my-task.html', EVENT_AND_TASK_PARAMS)

def add_task(request):
    if request.method == 'POST':
        form = AddTaskForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect(request.META['HTTP_REFERER'])

def register_event(request):
    if request.method == 'POST':
        form = RegisterEventForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect(request.META['HTTP_REFERER'])
