from django.contrib import admin
from .models import Company, Event, Task

admin.site.register(Company)
admin.site.register(Event)
admin.site.register(Task)