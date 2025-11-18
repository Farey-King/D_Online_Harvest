import email
from datetime import timedelta
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes
)

from django.conf import settings
from django.utils import timezone
from django.utils.timezone import now
from django.shortcuts import render
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework import status,permissions,generics
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
from django.db.models import Q,Sum,Avg,Count
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated


from .serializers import(
    AssignmentSerializer,
    CompletedSerializer,
    CoursePerformanceSerializer,
    CourseSerializer,
    InstructorEarningsSerializer,
    InstructorCourseSerializer,
    InstructorCourseCardSerializer,
    NotificationSerializer,
    OverdueSerializer,
    SignupSerializer,
    SigninSerializer,
    SignoutSerializer,
    RequestPasswordResetSerializer,
    ConfirmPasswordResetSerializer,
    ProfileSerializer,
    StudentDashboardSerializer,
    ContinueWatchingSerializer,
    CoursesListSerializer,
    UpcomingEventSerializer,
    UpcomingTaskSerializer,
    SummarySerializer,
)

from .models import( 
    Assignment,
    Completed,
    LessonProgress,
    Lesson,
    Notification,
    Overdue,
    Profile,
    Refund,
    SessionLog, 
    Signin,
    UpcomingEvent,
    UpcomingTask,
    User,
    Enrollment,
    Task,
    Course,
    InstructorEarning,
    Revenue
    
)
from harvest_lms import models
 

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

@extend_schema(
    tags=["Student Dashboard"],
    summary="Retrieve the logged-in student's dashboard data"
)
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
    
@extend_schema(
    tags=["Lessons"],
    summary="Mark a lesson as completed",
    description="Marks a lesson as completed, updates progress percentage, and sets course status to 'in-progress' or 'completed'."
)
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

@extend_schema(
    tags=["Courses"],
    summary="List all available courses"       
)
class CourseListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        courses = Course.objects.all()
        return Response(CourseSerializer(courses, many=True).data)
@extend_schema(
    tags=["Courses"],
    summary="Enroll in a course"
)
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
    
@extend_schema(
    tags=["Courses"],
    summary="Retrieve course details"
)
class CourseDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        course = Course.objects.filter(id=course_id).first()
        if not course:
            return Response({"message": "Course not found"}, status=404)

        return Response(CourseSerializer(course).data)

@extend_schema(
    tags=["Assignments"],
    summary="List and create assignments"
)
# Assignments
class AssignmentListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        return Assignment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema(
    tags=["Assignments"],
    summary="Retrieve, update, or delete an assignment"
)
class AssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        return Assignment.objects.filter(user=self.request.user)



@extend_schema(    tags=["Overdue"],
    summary="List overdue items"
)
#  Overdue
class OverdueListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OverdueSerializer
    queryset = Overdue.objects.all().order_by('-created_at')

class CompletedPagination(PageNumberPagination):
    """Pagination for completed items."""
    page_size = 5  # You can adjust this (e.g. 10 per page)
    page_size_query_param = 'page_size'
    max_page_size = 20

@extend_schema(
    tags=["Completed"],
    summary="List completed items",
    responses={200: CompletedSerializer}
)
#  Completed Summary
class CompletedListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CompletedSerializer
    queryset = Completed.objects.all().order_by('-created_at')
    pagination_class = CompletedPagination

@extend_schema(
    tags=["Completed Dashboard"],
    summary="Retrieve the logged-in student's completed dashboard data"
)
class StudentCompletedDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        completed_qs = Completed.objects.filter(user=user).order_by('-created_at')

        # Compute aggregate stats
        stats = completed_qs.aggregate(
            average_score=Avg('average_score'),
            test_completed=Count('id'),
            average_grade=Avg('average_grades')
        )

        # Convert numeric grade to letter grade
        avg_grade_value = stats['average_grade'] or 0
        grade_letter = self.get_grade_letter(avg_grade_value)

        # Apply pagination
        paginator = CompletedPagination()
        page = paginator.paginate_queryset(completed_qs, request)
        completed_data = CompletedSerializer(page, many=True).data

        # Final response structure
        response_data = {
            "average_score": round(stats['average_score'] or 0, 2),
            "test_completed": stats['test_completed'] or 0,
            "average_grade": grade_letter,
            "completed_items": completed_data,
        }

        # Add pagination metadata
        return paginator.get_paginated_response(response_data)

    def get_grade_letter(self, score):
        """Helper function to convert numeric grade to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        return "F"
    
@extend_schema(
    tags=["Overdue Dashboard"], 
    summary="Retrieve the logged-in student's overdue dashboard data"
)
class StudentOverdueDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Separate missed assignments and tests
        missed_assignments = Overdue.objects.filter(user=user, type='assignment').order_by('-days_overdue')
        missed_tests = Overdue.objects.filter(user=user, type='test').order_by('-days_overdue')

        response_data = {
            "missed_assignments": OverdueSerializer(missed_assignments, many=True).data,
            "missed_tests": OverdueSerializer(missed_tests, many=True).data,
        }

        return Response(response_data)

@extend_schema(
    tags=["Upcoming Events"],
    summary="List upcoming events"
)
class UpcomingEventListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        three_days = today + timedelta(days=3)
        seven_days = today + timedelta(days=7)

        # Get all courses the student is enrolled in
        enrolled_courses = Enrollment.objects.filter(user=user).values_list('course', flat=True)

        # Student's own events or related to enrolled courses
        events_qs = UpcomingEvent.objects.filter(
            Q(user=user) | Q(course__in=enrolled_courses)
        )

        # Group by due time
        due_soon_qs = events_qs.filter(
            due_day__lte=three_days, due_day__gte=today
        ).order_by('event_date')

        due_next_week_qs = events_qs.filter(
            due_day__gt=three_days, due_day__lte=seven_days
        ).order_by('event_date')

        data = {
            "summary": {
                "due_soon_count": due_soon_qs.count(),
                "due_next_week_count": due_next_week_qs.count(),
            },
            "due_soon": UpcomingEventSerializer(due_soon_qs, many=True).data,
            "due_next_week": UpcomingEventSerializer(due_next_week_qs, many=True).data,
        }

        return Response(data)
    
# Teacher Dashboard Cards
@extend_schema(
    tags=["Instructor Dashboard"],
    summary="Retrieve the logged-in instructor's dashboard card metrics"
)
class InstructorDashboardCardsView(APIView):
    """
    Returns the dashboard card metrics:
    - Total Earnings
    - Active Courses
    - Total Students
    Each with percentage growth from previous month.
    """

    def get_percentage_change(self, current, previous):
        if previous == 0:
            return 0.0
        return round(((current - previous) / previous) * 100, 2)

    def get(self, request):
        user = request.user

        today = now()
        this_month = today.replace(day=1)
        last_month_last_day = this_month - timedelta(days=1)
        last_month = last_month_last_day.replace(day=1)

        
        # TOTAL EARNINGS
        
        current_earnings = InstructorEarning.objects.filter(
            instructor=user,
            created_at__gte=this_month
        ).aggregate(total=Sum("amount"))["total"] or 0

        previous_earnings = InstructorEarning.objects.filter(
            instructor=user,
            created_at__range=[last_month, last_month_last_day]
        ).aggregate(total=Sum("amount"))["total"] or 0

        earnings_change = self.get_percentage_change(current_earnings, previous_earnings)

        
        #  ACTIVE COURSES
        
        current_courses = Course.objects.filter(author=user).count()

        previous_courses = Course.objects.filter(
            author=user,
            created_at__range=[last_month, last_month_last_day]
        ).count()

        courses_change = self.get_percentage_change(current_courses, previous_courses)

        
        #  TOTAL STUDENTS
        
        current_students = Enrollment.objects.filter(course__author=user).count()

        previous_students = Enrollment.objects.filter(course__author=user,enrolled_at__range=[last_month, last_month_last_day]).count()

        students_change = self.get_percentage_change(current_students, previous_students)

        # Final response
        response = {
            "cards": [
                {
                    "label": "Total Earnings",
                    "value": current_earnings,
                    "percentage_change": earnings_change
                },
                {
                    "label": "Active Courses",
                    "value": current_courses,
                    "percentage_change": courses_change
                },
                {
                    "label": "Total Students",
                    "value": current_students,
                    "percentage_change": students_change
                }
            ]
        }

        return Response(response)
# Course performance view graphs and stats
@extend_schema(
    tags=["Instructor Dashboard"],
    summary="Retrieve course performance metrics for the logged-in instructor"
)
class InstructorCoursePerformanceView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Returns course performance metrics:
    - Enrollment Trends
    - Refunds
    - Revenue Generated
    Over selectable chart

    """
    def get(self, request):
        user = request.user

        # Only instructor should access
        if user.role != "instructor":
            return Response({"detail": "Unauthorized"}, status=403)

        instructor_courses = Course.objects.filter(author=user)

        performance_data = []

        for course in instructor_courses:

            # COUNT ENROLLMENTS
            enrollment_count = Enrollment.objects.filter(course=course).count()

            # SUM REVENUE
            total_revenue = (
                Revenue.objects.filter(course=course)
                .aggregate(total=models.Sum("amount"))["total"] or 0
            )

            # SUM REFUND
            total_refunds = (
                Refund.objects.filter(course=course)
                .aggregate(total=models.Sum("amount"))["total"] or 0
            )

            performance_data.append({
                "course_title": course.title,
                "enrollment": enrollment_count,
                "revenue": total_revenue,
                "refund": total_refunds,
            })

        serializer = CoursePerformanceSerializer(performance_data, many=True)
        return Response(serializer.data)
@extend_schema(
    tags=["Instructor Tasks"],
)
class UpcomingTasksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        tasks = UpcomingTask.objects.filter(
            user=user,
            is_completed=False,
            due_date__gte=timezone.now()
        ).order_by("due_date")

        serializer = UpcomingTaskSerializer(tasks, many=True)
        return Response(serializer.data)
@extend_schema(
    tags=["Instructor Notifications"],
)
class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        notifications = Notification.objects.filter(user=user).order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)
@extend_schema(
    tags=["Instructor Notifications"],
)
# Mark notification as read
class MarkNotificationAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        notification.is_read = True
        notification.save()

        return Response({"detail": "Notification marked as read"})

@extend_schema(
    tags=["Instructor Earnings"],
)
class InstructorEarningsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        courses = Course.objects.filter(author=request.user)
        serializer = InstructorEarningsSerializer(courses, many=True)
        return Response(serializer.data)

@extend_schema(
    tags=["Instructor Courses"],
)
# CREATE Course
class InstructorCourseCreateView(CreateAPIView):
    serializer_class = InstructorCourseSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

@extend_schema(
    tags=["Instructor Courses"],
)
# LIST Courses (Instructor Dashboard Grid)
class InstructorCoursesListView(ListAPIView):
    serializer_class = InstructorCourseCardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Course.objects.filter(author=self.request.user)

@extend_schema(
    tags=["Instructor Courses"],
)
# VIEW Course Details
class InstructorCourseDetailView(RetrieveAPIView):
    serializer_class = InstructorCourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Course.objects.filter(author=self.request.user)

@extend_schema(
    tags=["Instructor Courses"],
)
# EDIT Course
class InstructorCourseEditView(UpdateAPIView):
    serializer_class = InstructorCourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Course.objects.filter(author=self.request.user)

@extend_schema(
    tags=["Instructor Courses"],
)
# DELETE Course
class InstructorCourseDeleteView(DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Course.objects.filter(author=self.request.user) 