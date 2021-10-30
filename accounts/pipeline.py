# social-app-authとgtest.modelsで作成したモデルを紐付ける
from .models import Profile

def save_profile(backend, user, response, *args, **kwargs):
    if Profile.objects.filter(user_id=user.id).count() == 0 :
        profile = Profile.objects.create(user=user)
        profile.save()