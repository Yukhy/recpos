from . import views
from django.urls import path

app_name = 'recpos'

urlpatterns = [
    path('', views.index, name="index"),
    path('mailbox', views.mailbox, name="mailbox"),
]
