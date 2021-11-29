from django.db import models
from accounts.models import Profile


class Company(models.Model):
    user_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="company")
    name = models.CharField(max_length=256)
    email = models.EmailField(blank=True, null=True)
    memo = models.CharField(blank=True, null=True, max_length=1024)

    def __str__(self):
        return self.name


class Event(models.Model):
    profile_id = models.IntegerField()
    company_id = models.IntegerField()
    title = models.CharField(max_length=256)
    start_date = models.DateField(max_length=128)
    end_date = models.DateField(max_length=128)
    detail = models.TextField(blank=True, null=True, max_length=1024)

    def __str__(self):
        return self.title

    def to_dict(self):
        return {'titel':self.title, 'start_date':self.start_date, 'end_date':self.end_date, 'detail':self.detail}



class Task(models.Model):
    profile_id = models.IntegerField()
    company_id = models.IntegerField()
    title = models.CharField(max_length=256)
    deadline = models.DateField(blank=True, null=True, max_length=128)
    detail = models.TextField(blank=True, null=True, max_length=1024)

    def __str__(self):
        return self.title

    def to_dict(self):
        return {'titel':self.title, 'deadline':self.deadline, 'detail':self.detail}