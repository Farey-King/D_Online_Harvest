import email
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes
)

from django.conf import settings
from django.utils import timezone
from django.shortcuts import render
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework import status,permissions
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q,Sum
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated


from .serializers import(
    CourseSerializer,
    SignupSerializer,
    SigninSerializer,
    SignoutSerializer,
    RequestPasswordResetSerializer,
    ConfirmPasswordResetSerializer,
    ProfileSerializer,
    StudentDashboardSerializer,
    ContinueWatchingSerializer,
    CoursesListSerializer,
    UpcomingTaskSerializer,
    SummarySerializer,
)

from .models import( 
    LessonProgress,
    Lesson,
    Profile,
    SessionLog, 
    Signin,
    User,
    Enrollment,
    Task,
    Course
)
 

@extend_schema(
    request=SignupSerializer,
    responses={201: SignupSerializer},
    description="Create a new user account."
)
class SignupView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

  # Mark verified automatically ✅
        user.email_verified = True
        user.is_active = True    # Important: allow login
        user.save()

        # Send welcome email (NOT verification email)
        send_mail(
                subject="Welcome to D Online Harvest LMS 🎉",
                message="Your account has been successfully created." \
                " Please proceed to sign in to your dashboard.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

        
        return Response(
                {"message": "Account created successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Signin API View
@extend_schema(
    request=SigninSerializer,
    responses={200: SigninSerializer},
    description="Authenticate a user and return JWT tokens."
)
class SigninView(APIView):
    def post(self, request):
        serializer = SigninSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, username=email, password=password)

        if not user:
            return Response({"detail": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
         # SAVE SIGNIN RECORD TO DATABASE
        Signin.objects.create(user=user, email=user.email)
        # Create session record
        SessionLog.objects.create(
            user=user,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.headers.get("User-Agent", "Unknown Device")
        )
        #  Determine Role
        if hasattr(user, "role"):  
            role = user.role
        else:  # If using Django groups
            if user.is_superuser:
                role = "admin"
            elif user.groups.filter(name="teacher").exists():
                role = "teacher"
            else:
                role = "student"

        # Custom Message Depending on Role
        if role == "admin":
            message = "Admin sign in successful"
        elif role == "teacher":
            message = "Teacher sign in successful"
        else:
            message = "Student sign in successful"
        return Response({
            "message": message,
            "email": user.email,            
            "user_id": user.id,
            "role": role,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)

# Signout API View
@extend_schema(
    request=SignoutSerializer,
    responses={200: None},
    description="Signout a user by blacklisting their refresh token."
)
class SignoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = SignoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()

            #  Update last session logout time
        last_session = request.user.sessions.last()
        if last_session:
                last_session.logout_time = timezone.now()
                last_session.save()

        return Response({"message": "Logout successful"}, status=200)
    
@extend_schema(
    request=RequestPasswordResetSerializer,
    responses={200: None},
    description="Request a password reset by sending an OTP to the user's email."
)
class RequestPasswordResetView(APIView):
    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "OTP sent to your email"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=ConfirmPasswordResetSerializer,
    responses={200: None},
    description="Confirm password reset using OTP and set a new password."
)
class ConfirmPasswordResetView(APIView):
    def post(self, request):
        serializer = ConfirmPasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password reset successful"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from .permissions import IsAdmin

class CreateCourseView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        # Only admins can reach here
        ...
        return Response({"message": "Course created successfully"})

class AdminOnlyView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        # Only admins can reach here
        ...
        return Response({"message": "Welcome, Admin!"})

from .permissions import IsTeacher

class UploadLessonView(APIView):
    permission_classes = [IsTeacher]

    def post(self, request):
        ...
        return Response({"message": "Lesson uploaded successfully"})

from .permissions import IsStudent

class EnrollCourseView(APIView):
    permission_classes = [IsStudent]

    def post(self, request):
        ...
        return Response({"message": "Enrolled in course successfully"})
    
@extend_schema(
    request=ProfileSerializer,
    responses={200: ProfileSerializer},
    description="Update user profile information."
)  
class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] 

    def put(self, request):
        profile, created = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Profile updated successfully",
            "profile": serializer.data
        })
# Logic to get user logs
@extend_schema(
    tags=['Debug'],
    summary="Admin lookup user by email (No Auth)",
    parameters=[
        OpenApiParameter(
            name="email",
            description="Email of the user you want to lookup",
            required=True,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
        )
    ], responses={200: ProfileSerializer},
    description="Lookup a user by email without authentication (for debugging purposes)."
)
@method_decorator(csrf_exempt, name='dispatch')
class UserLookupView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        email = request.query_params.get("email")
        if not email:
            return Response({"error": "email is required"}, status=400)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"message": "No user found"}, status=404)

        #  Ensure profile exists even for old accounts
        profile, created = Profile.objects.get_or_create(user=user)
        profile_data = ProfileSerializer(profile).data

        signin = Signin.objects.filter(user=user).values("email","login_time")

        return Response({
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "is_active": user.is_active,
                "role": user.role,
            },
            "profile": profile_data,
            "signin_logs": list(signin),
            
        })

class StudentDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Summary
        total_courses = Enrollment.objects.filter(user=user).count()
        completed_courses = Enrollment.objects.filter(user=user, status="completed").count()
        total_hours = Enrollment.objects.filter(user=user).aggregate(
            total=Sum('course__duration_hours')
        )['total'] or 0

        summary_data = {
            "total_courses": total_courses,
            "completed_courses": completed_courses,
            "total_hours": total_hours
        }
        summary = SummarySerializer(summary_data).data

        # Continue watching (In-progress courses)
        continue_watching = Enrollment.objects.filter(user=user, progress__lt=1.0)
        continue_watching_data = ContinueWatchingSerializer(continue_watching, many=True).data

        # All courses list
        courses = Enrollment.objects.filter(user=user)
        courses_data = CoursesListSerializer(courses, many=True).data

        # Upcoming tasks - due in the future
        tasks = Task.objects.filter(user=user, due_date__gte=timezone.now()).order_by('due_date')[:5]
        upcoming_tasks = UpcomingTaskSerializer(tasks, many=True).data

        # User section
        user_info = StudentDashboardSerializer(user).data

        return Response({
            "user": user_info,
            "summary": summary,
            "continue_watching": continue_watching_data,
            "courses": courses_data,
            "upcoming_tasks": upcoming_tasks
        })
class CompleteLessonView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        user = request.user

        lesson = Lesson.objects.filter(id=lesson_id).first()
        if not lesson:
            return Response({"message": "Lesson not found"}, status=404)

        # Ensure user is enrolled in the course
        enrollment = Enrollment.objects.filter(user=user, course=lesson.course).first()
        if not enrollment:
            return Response({"message": "Not enrolled in this course"}, status=403)

        # Mark lesson as completed
        LessonProgress.objects.update_or_create(
            user=user,
            lesson=lesson,
            defaults={"completed": True}
        )

        # Calculate progress
        total_lessons = lesson.course.lessons.count()
        completed_lessons = LessonProgress.objects.filter(
            user=user, lesson__course=lesson.course, completed=True
        ).count()

        progress_percent = (completed_lessons / total_lessons) * 100
        enrollment.progress = round(progress_percent, 2)

        # Update course status when finished
        if completed_lessons == total_lessons:
            enrollment.status = "completed"
        else:
            enrollment.status = "in-progress"

        enrollment.save()

        return Response({
            "message": "Lesson marked as completed",
            "progress": enrollment.progress,
            "status": enrollment.status,
        })
class CourseListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        courses = Course.objects.all()
        return Response(CourseSerializer(courses, many=True).data)

class EnrollInCourseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        user = request.user

        course = Course.objects.filter(id=course_id).first()
        if not course:
            return Response({"message": "Course not found"}, status=404)

        enrollment, created = Enrollment.objects.get_or_create(user=user, course=course)

        if not created:
            return Response({"message": "Already enrolled"}, status=400)

        return Response({"message": "Enrollment successful"})
    
    class CompleteLessonView(APIView):
        permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        user = request.user

        lesson = Lesson.objects.filter(id=lesson_id).first()
        if not lesson:
            return Response({"message": "Lesson not found"}, status=404)

        enrollment = Enrollment.objects.filter(user=user, course=lesson.course).first()
        if not enrollment:
            return Response({"message": "Not enrolled in this course"}, status=403)
        # mark lesson as completed
        LessonProgress.objects.update_or_create(
            user=user, lesson=lesson,
            defaults={"completed": True, "completed_at": timezone.now()}
                    )

        # update overall course progress
        total_lessons = lesson.course.lessons.count()
        completed_lessons = LessonProgress.objects.filter(
            user=user, lesson__course=lesson.course, completed=True
        ).count()

        enrollment.progress = (completed_lessons / total_lessons) * 100
        enrollment.save()

        return Response({"message": "Lesson completed", "progress": enrollment.progress})
    

class CourseDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        course = Course.objects.filter(id=course_id).first()
        if not course:
            return Response({"message": "Course not found"}, status=404)

        return Response(CourseSerializer(course).data)