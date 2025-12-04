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
        ("instructor", "Instructor"),
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
    video = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, choices=[('draft', 'Draft'), ('published', 'Published')], default='draft')

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
    CATEGORY_CHOICES = (
        ('front-end', 'Front-End Development'),
        ('back-end', 'Back-End Development'),
        ('full-stack', 'Full-Stack Development'),
        ('data-science', 'Data Science'),
        ('machine-learning', 'Machine Learning'),
        ('mobile-development', 'Mobile Development'),
        ('devops', 'DevOps'),
        ('cybersecurity', 'Cybersecurity'),
        ('cloud-computing', 'Cloud Computing'),
        ('other', 'Other'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='front-end')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in-progress')
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    progress = models.DecimalField(max_digits=4, decimal_places=2, default=0)  # example: 0.35 = 35%
    enrolled_at = models.DateTimeField(auto_now_add=True)

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

#Assignment Model
class Assignment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    course_note = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='assignments/')
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.user.email}"

class UpcomingEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upcoming_events')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='upcoming_events', null=True, blank=True)
    due_day = models.DateField()
    title = models.CharField(max_length=255)
    description = models.TextField()
    event_date = models.DateTimeField()
    duration  = models.CharField(max_length=50)  # e.g. "1 hr", "2 hrs"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Overdue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='overdues')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='overdues', null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    event_date = models.DateTimeField()
    days_overdue = models.PositiveIntegerField()
    type = models.CharField(max_length=50, choices=[('assignment', 'Assignment'), ('test', 'Test')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task.title} overdue by {self.days_overdue} days"
    
class Completed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    average_score = models.DecimalField(max_digits=5, decimal_places=2)
    test_completed = models.PositiveIntegerField()
    average_grades = models.DecimalField(max_digits=5, decimal_places=2)
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=1000)
    event_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.user.full_name}"

class InstructorEarning(models.Model):
    instructor = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.instructor.email} - {self.amount}"
    
class Revenue(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount}"


class Refund(models.Model):
    payment = models.OneToOneField(Revenue, on_delete=models.CASCADE, related_name='refund')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True, null=True)
    refunded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Refund for {self.payment.transaction_id}"

class UpcomingTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="upcoming_tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    task_type = models.CharField(max_length=50, choices=[
        ('assignment', 'Assignment'),
        ('grading', 'Grading'),
        ('event', 'Event'),
        ('course', 'Course'),
    ])
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.title}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    image = models.ImageField(upload_to='notifications/', blank=True, null=True)
    title = models.CharField(max_length=255)
    draft_date = models.CharField(max_length=100)
    message = models.CharField(max_length=1000)
    url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
   

    def __str__(self):
        return f"{self.user.full_name} - {self.title}"

class CourseView(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="views")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

class CourseSaved(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="saves")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

class Conversation(models.Model):
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="instructor_conversations")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="student_conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    is_blocked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('instructor', 'student')

    def __str__(self):
        return f"{self.instructor.username} ↔ {self.student.username}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"
    
class BasicInformation(models.Model):
    CATEGOTY_CHOICES = (
        ('front-end', 'Front-End Development'),
        ('back-end', 'Back-End Development'),
        ('full-stack', 'Full-Stack Development'),
        ('data-science', 'Data Science'),
        ('machine-learning', 'Machine Learning'),
        ('mobile-development', 'Mobile Development'),
        ('devops', 'DevOps'),
        ('cybersecurity', 'Cybersecurity'),
        ('cloud-computing', 'Cloud Computing'),
        ('other', 'Other'),
    )
    COURSE_CHOICES = (
        ('web-development', 'Web Development'),
        ('data-science', 'Data Science'),
        ('mobile-development', 'Mobile Development'),
        ('cloud-computing', 'Cloud Computing'),
        ('cybersecurity', 'Cybersecurity'),
        ('devops', 'DevOps'),
        ('machine-learning', 'Machine Learning'),
        ('other', 'Other'),
    )
    COURSE_LANGUAGE_CHOICES = (
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('typescript', 'TypeScript'),
        ('rust', 'Rust'),
        ('sql', 'SQL'),
        ('flutter', 'Flutter'),
        ('other', 'Other'),
    )
    SUBTITLE_LANGUAGE = (
        ('english', 'English'),
        ('french', 'French'),
        ('german', 'German'),
        ('spanish', 'Spanish'),
        ('chinese', 'Chinese'),
        ('japanese', 'Japanese'),
        ('other', 'Other'),
    )
    COURSE_LEVEL_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )
    DURATION_CHOICES = (
        ('short', 'Short (< 2 hours)'),
        ('medium', 'Medium (2-10 hours)'),
        ('long', 'Long (> 10 hours)'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="instructor")
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGOTY_CHOICES, default='front-end')
    course_sub_category = models.CharField(max_length=50, choices=COURSE_CHOICES, default='web-development')
    course_topics = models.TextField()
    course_language = models.CharField(max_length=50, choices=COURSE_LANGUAGE_CHOICES, default='python')
    subtitle_language = models.CharField(max_length=50, choices=SUBTITLE_LANGUAGE, default='english')
    course_level = models.CharField(max_length=50, choices=COURSE_LEVEL_CHOICES, default='beginner')
    duration = models.CharField(max_length=50, choices=DURATION_CHOICES, default='short')
    status = models.CharField(max_length=50, choices=[('draft', 'Draft'), ('published', 'Published')], default='draft')

class AdvancedInformation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="instructor_advanced")
    course_thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    course_trailer = models.FileField(upload_to='course_trailers/', blank=True, null=True)
    course_description = models.TextField()
    topics_covered = models.CharField(max_length=255)
    target_audience = models.CharField(max_length=255)
    course_requirements = models.CharField(max_length=255)

class CourseCurriculum(models.Model):
   CONTENT_TYPE_CHOICES = (
       ('video', 'Video'), 
       ('attach file', 'Attach File'), 
       ('captions', 'Captions'), 
       ('description', 'Description'),
       ('lecture notes', 'Lecture Notes'),
   )
   user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="instructor_curriculum")
   section_name = models.CharField(max_length=255)
   lecture_name = models.CharField(max_length=255,choices=CONTENT_TYPE_CHOICES, default='video')
   
class PublishCourse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="instructor_publish")
    welcome_message = models.TextField()
    congratulations_message = models.TextField()
    published_at = models.DateTimeField(null=True, blank=True)

class Transaction(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="customer_transactions")
    date = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=50, choices=[
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ])
    amount = models.DecimalField(max_digits=10, decimal_places=2)  


class TransactionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transaction_history")
    order_id = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    course_name = models.CharField(max_length=255)
    student= models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="student_transaction_history"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=[
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    ])
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


    def __str__(self):
        return f"{self.user.email} - {self.student.email} - {self.amount} - {self.transaction_id} - {self.status}"
    
class PurchaseHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchase_history")
    image = models.URLField(blank=True, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    author = models.CharField(max_length=200)
    purchase_date = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.user.email} purchased {self.title} on {self.purchase_date}"

class AdminDashboard(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="admin_dashboard")
    total_users = models.PositiveIntegerField(default=0)
    total_courses = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_enrollments = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Admin Dashboard - {self.admin.email}"

class AdminStatisticsDetail(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="admin_statistics")
    metric = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=15, decimal_places=2)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.metric} - {self.value} at {self.recorded_at}"
    
