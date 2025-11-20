from tkinter import Message
from rest_framework import serializers  # type: ignore
from django.contrib.auth import get_user_model
from .models import (
    AdvancedInformation,
    Completed,
    Conversation,
    Course,
    Notification,
    Overdue,
    PasswordResetOTP,
    UpcomingEvent,
    Assignment,
    UpcomingTask,
    User,
    SessionLog,
    Profile,
    Enrollment,
    Task,
    Lesson,
    Message,
    BasicInformation,
    CourseCurriculum,
    PublishCourse,
    TransactionHistory,
    PurchaseHistory

)
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import random

User = get_user_model()

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "full_name", "phone_number", "password", "confirm_password", "role"]
    
    def validate(self, data):
        errors = {}
        # Check format
        try:
            validate_email(data["email"])
        except ValidationError:
            errors["email"] = "Enter a valid email address."

        # Password match check
        if data["password"] != data["confirm_password"]:
            errors["password"] = "Passwords do not match."

        # Email uniqueness check
        if User.objects.filter(email=data["email"]).exists():
            errors["email"] = "User with this email already exists."

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    

class SigninSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class SignoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class SessionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionLog
        fields = ['user', 'ip_address', 'user_agent', 'login_time', 'logout_time']

class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email.")
        return value

    def save(self):
        user = User.objects.get(email=self.validated_data["email"])
        otp = str(random.randint(100000, 999999))
        PasswordResetOTP.objects.create(user=user, otp=otp)

        # Send Email
        user.email_user("Password Reset Code", f"Your OTP is: {otp}")
        return otp


class ConfirmPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, data):
        try:
            user = User.objects.get(email=data["email"])
            otp_record = PasswordResetOTP.objects.filter(user=user, otp=data["otp"]).last()
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid email"})

        if not otp_record or not otp_record.is_valid():
            raise serializers.ValidationError({"otp": "Invalid or expired OTP"})

        return data

    def save(self):
        user = User.objects.get(email=self.validated_data["email"])
        user.set_password(self.validated_data["new_password"])
        user.save()

class ProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", required=False)
    email = serializers.EmailField(source="user.email", required=False)
    class Meta:
        model = Profile
        fields = "__all__"

def update(self, instance, validated_data):
        # Extract user data
        user_data = validated_data.pop("user", {})

        # Update User fields
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        # Update Profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

# Student Dashboard Serializer
class StudentDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'role']
# Teacher Dashboard Serializer
class TeacherDashboardSerializer(serializers.ModelSerializer):  
    class Meta:
        model = User
        fields = ['full_name', 'email', 'role']
# Admin Dashboard Serializer
class AdminDashboardSerializer(serializers.ModelSerializer):  
    class Meta:
        model = User
        fields = ['full_name', 'email', 'role']
# Course Serializer
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    def create(self, validated_data):
        course = Course.objects.create(**validated_data)
        return course
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
class SummarySerializer(serializers.Serializer):
        total_courses = serializers.IntegerField()
        completed_courses = serializers.IntegerField()
        total_hours = serializers.DecimalField(max_digits=6, decimal_places=1)



class ContinueWatchingSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title')
    category = serializers.CharField(source='course.category')
    thumbnail = serializers.CharField(source='course.thumbnail')

    class Meta:
        model = Enrollment
        fields = ['course_title', 'category', 'thumbnail', 'progress']


class CoursesListSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='course.title')
    category = serializers.CharField(source='course.category')

    class Meta:
        model = Enrollment
        fields = ['title', 'category', 'status']


class UpcomingTaskSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title')

    class Meta:
        model = Task
        fields = ['title', 'course_title', 'due_date']
class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["id", "title", "content", "video_url", "order", "duration_minutes"]


class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["id", "title", "category", "image", "video", "duration_hours", "lessons"]


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseSerializer()

    class Meta:
        model = Enrollment
        fields = ["id", "status", "progress", "course"]

class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class UpcomingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpcomingEvent
        fields = '__all__'


class OverdueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Overdue
        fields = '__all__'


class CompletedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Completed
        fields = '__all__'

class CompletedItemSerializer(serializers.ModelSerializer):
    """Serializer for each completed item (test/assignment)."""
    class Meta:
        model = Completed
        fields = [
            'id',
            'title',
            'description',
            'event_date',
            'created_at',
            'average_score',
            'average_grades',
        ]


class CompletedDashboardSerializer(serializers.Serializer):
    """Serializer for top-level dashboard aggregates."""
    average_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    test_completed = serializers.IntegerField()
    average_grade = serializers.CharField()
    completed_items = serializers.ListField()


class OverdueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Overdue
        fields = [
            'id',
            'title',
            'description',
            'course',
            'event_date',
            'days_overdue',
            'type',
            'created_at'
        ]
class UpcomingEventSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = UpcomingEvent
        fields = [
            'id',
            'title',
            'description',
            'course_title',
            'due_day',
            'event_date',
            'duration',
            'created_at',
        ]
# for instructor cards dashboard
class InstuctorCardDashboardSerializer(serializers.ModelSerializer):
    label = serializers.CharField()
    value = serializers.FloatField()
    percentage_change = serializers.FloatField()
    
# Course Performance Serializer
class CoursePerformanceSerializer(serializers.Serializer):
    course_title = serializers.CharField()
    enrollment = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    refund = serializers.DecimalField(max_digits=10, decimal_places=2)

# Upcoming Task Serializer
class UpcomingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpcomingTask
        fields = ['id', 'title', 'description', 'task_type', 'due_date', 'is_completed']
        
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'created_at']

class InstructorEarningsSerializer(serializers.ModelSerializer):
    earnings = serializers.SerializerMethodField()
    views = serializers.SerializerMethodField()
    saved = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'image', 'video', 'price', 'earnings', 'views', 'saved']

    def get_earnings(self, obj):
        # Calculate total earnings from enrollments
        return sum(enrollment.price for enrollment in obj.enrollments.all())

    def get_views(self, obj):
        return obj.views.count()

    def get_saved(self, obj):
        return obj.saves.count()


class InstructorCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields ="__all__"


class InstructorCourseCardSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    students_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = "__all__"

    def get_rating(self, obj):
        # until reviews are implemented
        return 4.9

    def get_students_count(self, obj):
        return obj.enrollments.count()

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.username", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "sender", "sender_name", "content", "is_read", "timestamp"]


class ConversationListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.username", read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_messages = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "student_name", "last_message", "unread_messages"]

    def get_last_message(self, obj):
        last = obj.messages.last()
        return last.content if last else None

    def get_unread_messages(self, obj):
        return obj.messages.filter(is_read=False).count()


class ConversationDetailSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.username", read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "student_name", "messages"]

class StartConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['student', 'instructor']

class BasicInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicInformation
        fields = '__all__'

class AdvancedInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvancedInformation
        fields = '__all__'

class CourseCurriculumSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCurriculum
        fields = '__all__'

class PublishCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublishCourse
        fields = '__all__'

class TransactionHistorySerializer(serializers.Serializer):
    class Meta:
        model = TransactionHistory
        fields = '__all__'
    date = serializers.DateTimeField()
    course_name = serializers.CharField()
    total_students = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()

class EarningsDashboardSerializer(serializers.Serializer):
    total_earning = serializers.DecimalField(max_digits=10, decimal_places=2)
    current_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    withdrawals = serializers.DecimalField(max_digits=10, decimal_places=2)
    monthly_graph = serializers.ListField()
    yearly_graph = serializers.ListField()

class PurchaseHistorySerializer(serializers.Serializer):
    class Meta:
        model = PurchaseHistory
        fields = '__all__'

 