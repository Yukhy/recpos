from django.db import models
from accounts.models import Profile


class Company(models.Model):
    user_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="company")
    name = models.CharField(max_length=256)
    email = models.EmailField(blank=True, null=True)
    memo = models.CharField(blank=True, null=True, max_length=1024)

    def __str__(self):
        return self.name + " : " + self.user_profile.user.email

    def event_sort(self):
        events = self.event.all().order_by('stat_date_time')
        return events

    def task_sort(self):
        tasks = self.task.all().order_by('deadline')
        return tasks


class Event(models.Model):
    #owner_company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="event")
    title = models.CharField(max_length=256)
    start_date = models.DateField(blank=True, null=True, max_length=128)
    end_date = models.DateField(blank=True, null=True, max_length=128)
    detail = models.TextField(blank=True, null=True, max_length=1024)

    def __str__(self):
        return self.title



class Task(models.Model):
    #owner_company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="task")
    title = models.CharField(max_length=256)
    deadline = models.DateField(blank=True, null=True, max_length=128)
    detail = models.TextField(blank=True, null=True, max_length=1024)

    def __str__(self):
        return self.title