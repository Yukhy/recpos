from django.urls import path
from django.conf.urls import include
from .views import *

app_name = 'accounts'

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('auth/', include('social_django.urls', namespace='social')),
    path('', home, name='home'),
]