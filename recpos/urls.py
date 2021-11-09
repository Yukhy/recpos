from . import views
from django.urls import path

app_name = 'recpos'

urlpatterns = [
    path('', views.index, name="index"),
    path('login/', views.login, name="login"),
    path('mailbox/', views.mailbox, name="mailbox"),
    path('mailbox/<int:page>/', views.mailbox, name="mailbox"),
    #path('mailbox/<int:mail_id>/', views.mailbox, name="mail-detail"),に変更↓
    path('mailbox/detail/', views.mail_detail, name="mail-detail"),
    path('alias/mailbox/<int:page>/', views.alias, name="alias"),
    path('privacy-policy', views.privacy_policy, name="privacy-policy"),
]
