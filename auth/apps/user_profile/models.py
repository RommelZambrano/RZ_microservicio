from django.conf import settings
User = settings.AUTH_USER_MODEL
from djoser.signals import user_signed_up
from django.db import models
# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    picture = models.ImageField(upload_to='profile_pictures', blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    profile_info = models.TextField(max_length=500, blank=True, null=True)

    def post_user_signup(user, request, *args, **kwargs):

        user = user
        Profile.objects.create(user=user)
    
    user_signed_up.connect(post_user_signup)