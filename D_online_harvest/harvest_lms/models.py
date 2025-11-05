from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, full_name, email, phone_number, password=None):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(full_name=full_name, email=email, phone_number=phone_number)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, full_name, email, phone_number, password=None):
        user = self.create_user(full_name, email, phone_number, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=128)
    confirm_password = models.CharField(max_length=128, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    


class Signin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="signin_logs", null=True, blank=True)
    email = models.EmailField(blank=True)
    login_time = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return f"{self.email} - {self.login_time}"
    

class SessionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.login_time}"

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
