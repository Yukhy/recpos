from django.db import models
from accounts.models import Profile


class Company(models.Model):
    user_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="company")
    name = models.CharField(max_length=256)
    address = models.EmailField(blank=True)
    memo = models.CharField(max_length=1024)

class Event(models.Model):
    #owner_company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="event")
    title = models.CharField(max_length=256)
    start_date = models.DateField(blank=True, null=True, max_length=128)
    end_date = models.DateField(blank=True, null=True, max_length=128)
    detail = models.TextField(blank=True, null=True, max_length=1024)



class Task(models.Model):
    #owner_company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="task")
    title = models.CharField(max_length=256)
    deadline = models.DateField(blank=True, null=True, max_length=128)
    detail = models.TextField(blank=True, null=True, max_length=1024)
