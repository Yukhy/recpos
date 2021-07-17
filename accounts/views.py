from django.shortcuts import render
from django.http import HttpResponseRedirect

# Create your views here.

def LoginView(request):
    return HttpResponseRedirect('social:begin', kwargs=dict(backend='google-oauth2'))

def index(request):
    return render(request, 'accounts/index.html')