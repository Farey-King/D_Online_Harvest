
from email.message import Message
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import( AdvancedInformation,
                    Completed,
                    Conversation,
                    Lesson, 
                    LessonProgress, 
                    Overdue, 
                    Profile, 
                    Revenue, 
                    Review,
                    Refund,
                    SessionLog, UpcomingEvent, Assignment,
                    User,
                    Signin,
                    Course,
                    Task,
                    Enrollment,
                    CourseView,
                    CourseSaved,
                    Message,
                    BasicInformation,
                    CourseCurriculum,
                    PublishCourse,
                    Transaction,
                    Notification,
                    ShopingCart,
                    Checkout,
                    VerificationCode
                    
                    

)
admin.site.register(VerificationCode)
admin.site.register(Checkout)
admin.site.register(ShopingCart)
admin.site.register(AdvancedInformation)
admin.site.register(BasicInformation)
admin.site.register(CourseCurriculum)
admin.site.register(PublishCourse)
admin.site.register(CourseSaved)
admin.site.register(CourseView)
admin.site.register(Transaction)
admin.site.register(Notification)


admin.site.register(Revenue)
admin.site.register(Refund)


User = get_user_model()

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "email_verified","role", "full_name", "phone_number", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("full_name", "phone_number")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "phone_number", "password1", "password2", "is_staff", "is_active"),
        }),
    )

    search_fields = ("email", "full_name", "phone_number")
    ordering = ("email",)

# Signin
@admin.register(Signin)
class SigninAdmin(admin.ModelAdmin):
    list_display = ("email",)
    search_fields = ("email",) 
# SessionLog 
@admin.register(SessionLog)
class SessionLogAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "user_agent", "login_time", "logout_time")
    list_filter = ("login_time", "logout_time")
    search_fields = ("user__email", "ip_address", "user_agent")


admin.site.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "image", "gender", "phone", "address", "date_of_birth")
    search_fields = ("user__email",)
admin.site.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "created_at")
    search_fields = ("title",)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "due_date")
    search_fields = ("title", "description", "assigned_to__full_name")
    list_filter = ("title", "due_date")

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course",  "progress")
    search_fields = ("user__full_name", "course__title")
    list_filter = ("user", "course")

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "completed")
    search_fields = ("user__full_name", "lesson__title")
    list_filter = ("completed","user","lesson")

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    search_fields = ("title", "course__title")
    list_filter = ("course",)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "rating", "created_at")
    search_fields = ("user__full_name", "course__title")
    list_filter = ("course", "rating")

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'course', 'due_date', 'created_at')
    search_fields = ('title', 'user__email')
    list_filter = ('course', 'due_date')



@admin.register(UpcomingEvent)
class UpcomingEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'course', 'due_day', 'event_date', 'duration', 'created_at')
    list_filter = ('course', 'due_day', 'user')
    search_fields = ('title', 'description', 'course__title', 'user__username', 'user__email')
    ordering = ('-event_date',)


@admin.register(Completed)
class CompletedAdmin(admin.ModelAdmin):
    list_display = ('title',"user", 'average_score', 'test_completed', 'average_grades', 'event_date')
    search_fields = ('title',)
    list_filter = ('event_date',)

@admin.register(Overdue)
class OverdueAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'course', 'type', 'days_overdue', 'event_date', 'created_at')
    list_filter = ('type', 'course', 'days_overdue')
    search_fields = ('title', 'description', 'course', 'user__username', 'user__email')
    ordering = ('-created_at',)

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'content', 'is_read', 'timestamp')
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'instructor', 'student', 'created_at', 'is_blocked')
    list_filter = ('is_blocked', 'created_at')
    search_fields = ('instructor__username', 'student__username')
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'short_content', 'is_read', 'timestamp')
    list_filter = ('is_read', 'timestamp', 'sender')
    search_fields = ('sender__username', 'content')
    readonly_fields = ('timestamp',)

    def short_content(self, obj):
        return obj.content[:40] + ("..." if len(obj.content) > 40 else "")
    short_content.short_description = "Content"
