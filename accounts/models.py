from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    alias = models.EmailField(max_length=50, blank=True, default='')
    gmail_api_token = models.CharField(blank=True, null=True, max_length=1024, default='')
    messages = models.TextField(blank=True, null=True, default='{"messages": []}')
    labels = models.TextField(blank=True, null=True, default='{"labels": []}')
    last_history_id = models.CharField(blank=True, null=True, max_length=1024, default='')

    def __str__(self):
        return self.user.email

# userが新規作成sされたときにProfileを作成する
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    try:
        instance.profile.save()
    # adminサイトでのログイン時、ObjectDoesNotExistエラーが発生するため。
    except ObjectDoesNotExist:
        Profile.objects.create(user=instance)