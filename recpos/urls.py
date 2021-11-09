from . import views
from django.urls import path

app_name = 'recpos'

urlpatterns = [
    path('', views.index, name="index"),
    path('login/', views.login, name="login"),
    path('mailbox/', views.mailbox, name="mailbox"),
    path('mailbox/<int:page>/', views.mailbox, name="mailbox"),
    path('mailbox/detail/', views.mail_detail, name="mail-detail"),
    path('mailbox/detail/<int:index>/', views.mail_detail, name="mail-detail"),
    path('mailbox/<str:label>/', views.mailbox, name="mailbox"),
    path('mailbox/<str:label>/<int:page>/', views.mailbox, name="mailbox"),
    path('alias/mailbox/', views.alias, name="alias"),
    path('alias/mailbox/<int:page>/', views.alias, name="alias"),
    path('alias/mailbox/<str:label>/', views.alias, name="alias"),
    path('alias/mailbox/<str:label>/<int:page>/', views.alias, name="alias"),
    path('privacy-policy', views.privacy_policy, name="privacy-policy"),
]
