from django.db import models
from accounts.models import Profile


class Company(models.Model):
    user_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="company")
    company_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256)
    email = models.EmailField(blank=True)
    memo = models.CharField(max_length=1024)

    def __str__(self):
        return self.name + " : " + self.user_id.first_name + " " + self.user_id.last_name

    def event_sort(self):
        events = self.event.all().order_by('stat_date_time')
        return events

    def task_sort(self):
        tasks = self.task.all().order_by('deadline')
        return tasks


class Event(models.Model):
    owner_company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="event")
    event_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256)
    start_date_time = models.DateField(blank=True, null=True, max_length=128)
    end_date_time = models.DateField(blank=True, null=True, max_length=128)
    url = models.URLField(max_length=512)
    memo = models.TextField(blank=True, null=True, max_length=1024)

    def __str__(self):
        return self.company_id.name + " : " + self.name


class Task(models.Model):
    owner_company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="task")
    task_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256)
    deadline = models.DateField(blank=True, null=True, max_length=128)
    url = models.URLField(max_length=256)
    memo = models.TextField(blank=True, null=True, max_length=1024)

    def __str__(self):
        return self.company_id.name + " : " + self.name