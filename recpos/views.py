from django.shortcuts import render


# Create your views here.


def index(request):
    return render(request, 'recpos/index.html')

def mailbox(request):
    return render(request, 'recpos/mailbox.html')

def login(request):
    return render(request, 'recpos/tmpLogin.html')