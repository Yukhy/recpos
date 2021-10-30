from django.urls import path
from django.conf.urls import include
from .views import *

app_name = 'accounts'

urlpatterns = [
    path('', include('django.contrib.auth.urls'), name='login'),
    path('auth/', include('social_django.urls', namespace='social')),
]