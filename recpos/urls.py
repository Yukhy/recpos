from . import views
from django.urls import path

app_name = 'recpos'

urlpatterns = [
    path('', views.index, name="index"),
    path('signup/', views.signup, name="signup"),
    path('login/', views.login, name="login"),
    path('mailbox/<int:num>/', views.mailbox, name="mailbox"),
    path('privacy-policy', views.privacy_policy, name="privacy-policy"),
]
