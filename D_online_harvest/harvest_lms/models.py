from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
import uuid

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
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("teacher", "Teacher"),
        ("student", "Student"),
    )
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=True)
    phone_number = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=128)
    confirm_password = models.CharField(max_length=128, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} - {self.role}"
    


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

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return timezone.now() <= self.created_at + timedelta(minutes=10)
    

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100)
    image = models.URLField(blank=True, null=True)
    duration_hours = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="courses")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    

    def __str__(self):
        return f"{self.user.email}'s Profile"


class Enrollment(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in-progress')
    progress = models.DecimalField(max_digits=4, decimal_places=2, default=0)  # example: 0.35 = 35%

    def __str__(self):
        return f"{self.user} → {self.course}"


class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject= models.ForeignKey(Course, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255)
    due_date = models.DateField()

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey('Course', related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    duration = models.CharField(max_length=50)  # e.g. "3 min", "1 hr"
    video_url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField(default=1)  # Lesson ordering
    duration_minutes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'lesson')


class Review(models.Model):
    course = models.ForeignKey('Course', related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)  # 1 to 5
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} review for {self.course}"