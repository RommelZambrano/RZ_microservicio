from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin, BaseUserManager
from slugify import slugify
from core.producer import producer
import json, uuid, re

class UserAccountManager(BaseUserManager):
    
    def create_user(self, email, password=None, **extra_fields):

        def create_slug(username):
            pattern_special_character = r'\badamin\b|[!@#$%^&*()=;~,.?":{}|<>]\s'
            if re.search(pattern_special_character, username):
                raise ValueError('Username cannot contain special characters')
            username = re.sub(pattern_special_character, '', username)
            return slugify(username)


        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)
        extra_fields['slug'] = create_slug(extra_fields['username'])
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        item={}
        item['id'] = user.id
        item['email'] = user.email
        item['username'] = user.username
        producer.produce(
            'auth',
            key='create_user',
            value=json.dumps(item).encode('utf-8')
        )
        producer.flush()
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        user = self.create_user(email, password, **extra_fields)
        user.is_superuser = True
        user.is_staff = True
        user.role = 'Admin'
        user.verified = True
        user.save(using=self._db)

        return user
    
class UserAccount(AbstractUser, PermissionsMixin):
    roles =(
        ('Admin', 'Admin'),
        ('Manager', 'Manager'),
        ('Teacher', 'Teacher'),
        ('Student', 'Student')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_online = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    role = models.CharField(max_length=50, choices=roles, default='Student')
    verified = models.BooleanField(default=False)

    courses = models.ManyToManyField('course.Course', related_name='students', blank=True)

    objects = UserAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def save(self, *args, **kwargs):
        self.slug = slugify(self.username)
        counter = 1
        while UserAccount.objects.filter(slug=self.slug).exists():
            self.slug = f'{self.slug}-{counter}'
            counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email