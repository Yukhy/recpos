from . import views
from django.urls import path

app_name = 'recpos'

urlpatterns = [
    path('', views.index, name="index"),
    path('login/', views.login, name="login"),
    path('mailbox/', views.mailbox, name="mailbox"),
    path('mailbox/<int:page>/', views.mailbox, name="mailbox"),
    path('mailbox/detail/', views.mail_detail, name="mail-detail"),
    path('mailbox/detail/<int:index>/<str:prev>/', views.mail_detail, name="mail-detail"),
    path('star/', views.star, name='star'),
    path('star/<int:index>/<str:prev>', views.star, name='star'),
    path('unstar/', views.unstar, name='unstar'),
    path('unstar/<int:index>/<str:prev>', views.unstar, name='unstar'),
    path('trash/', views.trash, name='trash'),
    path('trash/<int:index>/<str:prev>', views.trash, name='trash'),
    path('putback/', views.putback, name='putback'),
    path('putback/<int:index>/<str:prev>', views.putback, name='putback'),
    path('mailbox/<str:label>/', views.mailbox, name="mailbox"),
    path('mailbox/<str:label>/<int:page>/', views.mailbox, name="mailbox"),
    path('alias/mailbox/', views.alias, name="alias"),
    path('alias/mailbox/<int:page>/', views.alias, name="alias"),
    path('alias/mailbox/<str:label>/', views.alias, name="alias"),
    path('alias/mailbox/<str:label>/<int:page>/', views.alias, name="alias"),
    path('privacy-policy/', views.privacy_policy, name="privacy-policy"),
    path('opensource-licenses/', views.opensource, name="open-source"),
    path("company-list/", views.company_list, name="company-list"),
    path("my-task/", views.my_task, name="my-task"),

    path("add-task/", views.add_task, name="add-task"),
    path("register-event/", views.register_event, name="register-event"),
]
