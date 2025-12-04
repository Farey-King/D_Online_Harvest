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
from django.shortcuts import get_object_or_404, render
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.apps import apps
from rest_framework.response import Response
from rest_framework import status,permissions,generics
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
from django.db.models import Q,Sum,Avg,Count
from django.db.models.functions import TruncWeek, TruncMonth, TruncYear
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated


from .serializers import(
    AdvancedInformationSerializer,
    AssignmentSerializer,
    CompletedSerializer,
    CourseCurriculumSerializer,
    CoursePerformanceSerializer,
    CourseSerializer,
    InstructorEarningsSerializer,
    InstructorCourseSerializer,
    InstructorCourseCardSerializer,
    NotificationSerializer,
    OverdueSerializer,
    PublishCourseSerializer,
    SignupSerializer,
    SigninSerializer,
    SignoutSerializer,
    RequestPasswordResetSerializer,
    ConfirmPasswordResetSerializer,
    ProfileSerializer,
    StudentDashboardSerializer,
    ContinueWatchingSerializer,
    CoursesListSerializer,
    TransactionHistorySerializer,
    TransactionSerializer,
    UpcomingEventSerializer,
    UpcomingTaskSerializer,
    SummarySerializer,
    ConversationListSerializer,
    ConversationDetailSerializer,
    MessageSerializer,
    StartConversationSerializer,
    BasicInformationSerializer,
    EarningsDashboardSerializer,
    PurchaseHistorySerializer,
    AdminDashboardSerializer,
)

from .models import( 
    Assignment,
    Completed,
    Conversation,
    CourseCurriculum,
    Message,
    LessonProgress,
    Lesson,
    Notification,
    Overdue,
    Profile,
    Refund,
    SessionLog, 
    Signin,
    Transaction,
    UpcomingEvent,
    UpcomingTask,
    User,
    Enrollment,
    Task,
    Course,
    InstructorEarning,
    Revenue,
    BasicInformation,
    AdvancedInformation,
    TransactionHistory,
    PurchaseHistory
    
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
            elif user.groups.filter(name="instructor").exists():
                role = "instructor"
            else:
                role = "student"

        # Custom Message Depending on Role
        if role == "admin":
            message = "Admin sign in successful"
        elif role == "instructor":
            message = "Instructor sign in successful"
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

class IsAdminOrSuperuser(IsAuthenticated):
    """Custom permission to only allow admin users"""
    def has_permission(self, request, view):
        return (super().has_permission(request, view) and 
                (request.user.is_staff or request.user.is_superuser))

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
            enrolled_at__gte=this_month
        ).aggregate(total=Sum("amount"))["total"] or 0

        previous_earnings = InstructorEarning.objects.filter(
            instructor=user,
            enrolled_at__range=[last_month, last_month_last_day]
        ).aggregate(total=Sum("amount"))["total"] or 0

        earnings_change = self.get_percentage_change(current_earnings, previous_earnings)

        
        #  ACTIVE COURSES
        
        current_courses = Course.objects.filter(author=user).count()

        previous_courses = Course.objects.filter(
            author=user,
            enrolled_at__range=[last_month, last_month_last_day]
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
        notifications = Notification.objects.filter(user=user).values('title','message')
        return Response(list(notifications))    
    

@extend_schema(
    tags=["Instructor Notifications"],
    summary="Mark a notification as read"
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
    tags=["Admin Notifications"],
    summary="Post a notification for the logged-in user",
    request = NotificationSerializer,
    responses = NotificationSerializer,


)# Post a notification 
class NotificationView(APIView):
        permission_classes = [IsAdminOrSuperuser]

        def post(self, request):
           data = request.data
           serializer = NotificationSerializer(data=data)
           serializer.is_valid(raise_exception=True)
           serializer.save()


           return Response(serializer.data)
        

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

@extend_schema(
    tags=["Conversations and Messaging"],
)
# List all conversations (chat list)
class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = Conversation.objects.filter(instructor=request.user)
        serializer = ConversationListSerializer(conversations, many=True)
        return Response(serializer.data)

@extend_schema(
    tags=["Conversations and Messaging"],
)
# Fetch conversation thread
class ConversationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, convo_id):
        convo = get_object_or_404(Conversation, id=convo_id, instructor=request.user)
        serializer = ConversationDetailSerializer(convo)
        convo.messages.filter(is_read=False).update(is_read=True)
        return Response(serializer.data)

@extend_schema(
    tags=["Conversations and Messaging"],
    request=MessageSerializer,
    responses=MessageSerializer,
)
# Send a message
class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, convo_id):
        convo = get_object_or_404(Conversation, id=convo_id)
        msg = Message.objects.create(
            conversation=convo,
            sender=request.user,
            content=request.data.get("content")
        )
        return Response(MessageSerializer(msg).data)

@extend_schema(
    tags=["Conversations and Messaging"],
    request=StartConversationSerializer,
    responses=StartConversationSerializer,
)
# Start a new conversation
class StartConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        student_id = request.data.get("student_id")
        convo, created = Conversation.objects.get_or_create(
            instructor=request.user,
            student_id=student_id
        )
        return Response({"conversation_id": convo.id, "new": created})

@extend_schema(
    tags=["Conversations and Messaging"],
)   
# Delete conversation
class DeleteConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, convo_id):
        convo = get_object_or_404(Conversation, id=convo_id, instructor=request.user)
        convo.delete()
        return Response({"detail": "Conversation deleted"})

@extend_schema(
    tags=["Conversations and Messaging"],
)
# Block user
class BlockConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, convo_id):
        convo = get_object_or_404(Conversation, id=convo_id, instructor=request.user)
        convo.is_blocked = True
        convo.save()
        return Response({"detail": "User blocked"})
    
@extend_schema(
    tags=["Basic Information"],
    request=BasicInformationSerializer,
    responses=BasicInformationSerializer,
)
class BasicInformationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BasicInformationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response({
            "message": "Basic information saved successfully",
            "data": serializer.data
        })

@extend_schema(
    tags=["Advanced Information"],
    request=AdvancedInformationSerializer,
    responses=AdvancedInformationSerializer,
)
class AdvancedInformationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AdvancedInformationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response({
            "message": "Advanced information saved successfully",
            "data": serializer.data
        })

@extend_schema(
    tags=["Course Curriculum"],
    request=CourseCurriculumSerializer,
    responses=CourseCurriculumSerializer,
)
class CourseCurriculumView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CourseCurriculumSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response({
            "message": "Course curriculum saved successfully",
            "data": serializer.data
        })

@extend_schema(
    tags=["Course Curriculum"],
    request=CourseCurriculumSerializer,
    responses=CourseCurriculumSerializer,
)
class CourseCurriculumUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            curriculum = CourseCurriculum.objects.get(pk=pk, user=request.user)
        except CourseCurriculum.DoesNotExist:
            return Response({"error": "Curriculum not found"}, status=404)

        serializer = CourseCurriculumSerializer(curriculum, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Course curriculum updated successfully",
            "data": serializer.data
        })

    def patch(self, request, pk):
        try:
            curriculum = CourseCurriculum.objects.get(pk=pk, user=request.user)
        except CourseCurriculum.DoesNotExist:
            return Response({"error": "Curriculum not found"}, status=404)

        serializer = CourseCurriculumSerializer(curriculum, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Course curriculum partially updated",
            "data": serializer.data
        })

@extend_schema(
    tags=["Course Curriculum"],
)
class CourseCurriculumDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            curriculum = CourseCurriculum.objects.get(pk=pk, user=request.user)
        except CourseCurriculum.DoesNotExist:
            return Response({"error": "Curriculum not found"}, status=404)

        curriculum.delete()

        return Response({"message": "Course curriculum deleted successfully"}, status=200)

@extend_schema(
    tags=["Publish Course"],
    request=PublishCourseSerializer,
    responses=PublishCourseSerializer,
)
class PublishCourseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PublishCourseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response({
            "message": "Course published successfully",
            "data": serializer.data
        })
@extend_schema(
    tags=["Instructor Earnings Dashboard"],
    summary="Retrieve the logged-in instructor's earnings dashboard data"
)
class EarningsDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        instructor = request.user

        # BASE QUERY 
        base_qs = Revenue.objects.filter(course__author=instructor)

        # CARD METRICS 

        total_earning = base_qs.aggregate(total=Sum("amount"))["total"] or 0
        current_balance = total_earning  # Until withdrawal system exists

        last_7_days = timezone.now() - timedelta(days=7)
        pending_payout = base_qs.filter(enrolled_at__gte=last_7_days)\
                                .aggregate(total=Sum("amount"))["total"] or 0

        total_revenue = total_earning  # Same metric for now

        card_data = {
            "total_earning": {"amount": total_earning, "percentage_change": 36},
            "current_balance": {"amount": current_balance, "percentage_change": -14},
            "pending_payout": {"amount": pending_payout, "percentage_change": 36},
            "total_revenue": {"amount": total_revenue, "percentage_change": 36},
        }

        # WEEKLY GRAPH (Last 12 weeks) 
        weekly = base_qs.annotate(week=TruncWeek("enrolled_at")) \
                        .values("week") \
                        .annotate(total=Sum("price")) \
                        .order_by("week")

        weekly_chart = [
            {"week": str(row["week"].date()), "earning": float(row["total"])}
            for row in weekly
        ]

        # MONTHLY GRAPH (Jan–Dec) 
        monthly = base_qs.annotate(month=TruncMonth("enrolled_at")) \
                         .values("month") \
                         .annotate(total=Sum("price")) \
                         .order_by("month")

        monthly_chart = []
        for m in range(1, 12 + 1):
            month_total = 0
            for row in monthly:
                if row["month"].month == m:
                    month_total = float(row["total"])
            monthly_chart.append({
                "month": m,
                "earning": month_total
            })

        # YEARLY GRAPH (Last 5 years) 
        yearly = base_qs.annotate(year=TruncYear("enrolled_at")) \
                        .values("year") \
                        .annotate(total=Sum("price")) \
                        .order_by("year")

        yearly_chart = [
            {"year": row["year"].year, "earning": float(row["total"])}
            for row in yearly
        ]

        return Response({
            "message": "Earnings dashboard fetched successfully",
            "cards": card_data,
            "earning_overtime": {
                "weekly": weekly_chart,
                "monthly": monthly_chart,
                "yearly": yearly_chart,
            }
        })
# Instructor Transaction Summary Table
@extend_schema(
    tags=["Instructor Earnings Dashboard"],
    summary="Retrieve transaction summary for the logged-in instructor"

)

class TransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        courses = Course.objects.all()
        summary_data = []

        for course in courses:
            # total enrolled students
            total_students = course.enrollments.count()

            # sum of all successful payments for this course
            total_amount = TransactionHistory.objects.filter(
                course=course,
                status="success"
            ).aggregate(total=Sum("amount"))["total"] or 0

            # pick a date: latest transaction date or course enrollment date
            latest_transaction = TransactionHistory.objects.filter(course=course).order_by("-enrolled_at").first()
            date_value = latest_transaction.enrolled_at if latest_transaction else course.enrolled_at

            summary_data.append({
                "date": date_value,
                "course_name": course.title,
                "total_students": total_students,
                "total_amount": total_amount,
                "status": "Active" 
            })

        serializer = TransactionHistorySerializer(summary_data, many=True)
        return Response({"summary": serializer.data})
    
 # Purchase History View   
@extend_schema(
    tags=["Purchase History"],
    summary="Retrieve the logged-in user's purchase history"
)
class PurchaseHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Return the authenticated user's purchase history
        purchases = PurchaseHistory.objects.filter(user=request.user).order_by('-id')
        serializer = PurchaseHistorySerializer(purchases, many=True)
        return Response(serializer.data)

class AdminDashboardView(APIView):
    permission_classes = [IsAdminOrSuperuser]

    def get(self, request):
        period = request.query_params.get('period', 'week')

        data = {
            "top_statistics": self.get_top_statistics(period),
            "commission_cards": self.get_commission_cards(),
            "user_growth_chart": self.get_user_growth_chart(period),
            "top_performing_courses": self.get_top_performing_courses()
        }

        return Response(data, status=status.HTTP_200_OK)

    # ---------------------------------------------
    # TOP STATISTICS
    # ---------------------------------------------
    def get_top_statistics(self, period):
        end = timezone.now()

        if period == "week":
            current_start = end - timedelta(days=7)
            previous_start = end - timedelta(days=14)
        elif period == "month":
            current_start = end - timedelta(days=30)
            previous_start = end - timedelta(days=60)
        else:
            current_start = end - timedelta(days=365)
            previous_start = end - timedelta(days=730)

        # Students
        total_students = User.objects.filter(role="student").count()
        current_students = User.objects.filter(role="student", date_joined__gte=current_start).count()
        previous_students = User.objects.filter(
            role="student",
            date_joined__gte=previous_start,
            date_joined__lt=current_start
        ).count()
        student_growth = self.calculate_growth(current_students, previous_students)

        # Instructors
        total_instructors = User.objects.filter(Q(role="instructor") | Q(is_staff=True)).count()
        current_instructors = User.objects.filter(
            Q(role="instructor") | Q(is_staff=True),
            date_joined__gte=current_start
        ).count()
        previous_instructors = User.objects.filter(
            Q(role="instructor") | Q(is_staff=True),
            date_joined__gte=previous_start,
            date_joined__lt=current_start
        ).count()
        instructor_growth = self.calculate_growth(current_instructors, previous_instructors)

        # Courses
        Course = apps.get_model("harvest_lms", "Course")

        total_courses = Course.objects.filter(status="published").count()
        current_courses = Course.objects.filter(
            status="published",
            created_at__gte=current_start
        ).count()
        previous_courses = Course.objects.filter(
            status="published",
            created_at__gte=previous_start,
            created_at__lt=current_start
        ).count()
        course_growth = self.calculate_growth(current_courses, previous_courses)

        # Revenue
        Enrollment = apps.get_model("harvest_lms", "Enrollment")

        total_revenue = Enrollment.objects.aggregate(total=Sum("price"))["total"] or 0
        current_revenue = Enrollment.objects.filter(
            enrolled_at__gte=current_start
        ).aggregate(total=Sum("price"))["total"] or 0
        previous_revenue = Enrollment.objects.filter(
            enrolled_at__gte=previous_start,
            enrolled_at__lt=current_start
        ).aggregate(total=Sum("price"))["total"] or 0
        revenue_growth = self.calculate_growth(current_revenue, previous_revenue)

        # Rating
        Review = apps.get_model("harvest_lms", "Review")
        average_rating = Review.objects.aggregate(avg=Avg("rating"))["avg"] or 0
        # Compute average rating for the current and previous period for growth calculation
        current_average_rating = (
            Review.objects.filter(created_at__gte=current_start)
            .aggregate(avg=Avg("rating"))["avg"] or 0
        )
        previous_average_rating = (
            Review.objects.filter(
                created_at__gte=previous_start,
                created_at__lt=current_start,
            )
            .aggregate(avg=Avg("rating"))["avg"] or 0
        )
        rating_growth = self.calculate_growth(
            float(current_average_rating), float(previous_average_rating)
        )

        return {
            "total_students": total_students,
            "student_growth": student_growth,
            "total_instructors": total_instructors,
            "instructor_growth": instructor_growth,
            "active_courses": total_courses,
            "course_growth": course_growth,
            "total_revenue": float(total_revenue),
            "revenue_growth": revenue_growth,
            "average_rating": round(float(average_rating), 2),
            "rating_growth": rating_growth,
        }

    # ---------------------------------------------
    # COMMISSION CARDS
    # ---------------------------------------------
    def get_commission_cards(self):
        Enrollment = apps.get_model("harvest_lms", "Enrollment")

        PLATFORM_RATE = 0.20

        total_revenue = Enrollment.objects.aggregate(total=Sum("price"))["total"] or 0

        lifetime_commission = total_revenue * PLATFORM_RATE
        instructor_share = total_revenue * (1 - PLATFORM_RATE)

        return {
            "lifetime_courses_commission": float(lifetime_commission),
            "lifetime_received_commission": float(instructor_share),
            "lifetime_pending_commission": float(lifetime_commission * 0.10),  # Example
        }

    # ---------------------------------------------
    # USER GROWTH CHART
    # ---------------------------------------------
    def get_user_growth_chart(self, period):
        Course = apps.get_model("harvest_lms", "Course")

        end = timezone.now()

        if period == "week":
            interval = 1
            points = 7
        elif period == "month":
            interval = 2.5
            points = 12
        else:
            interval = 30
            points = 12

        data = []

        for i in range(points):
            start = end - timedelta(days=(i + 1) * interval)
            stop = end - timedelta(days=i * interval)

            students = User.objects.filter(
                role="student", date_joined__gte=start, date_joined__lt=stop
            ).count()

            instructors = User.objects.filter(
                Q(role="instructor") | Q(is_staff=True),
                date_joined__gte=start,
                date_joined__lt=stop,
            ).count()

            courses = Course.objects.filter(
                created_at__gte=start, created_at__lt=stop
            ).count()

            data.insert(
                0,
                {
                    "label": stop.strftime("%b %d"),
                    "students": students,
                    "instructors": instructors,
                    "courses": courses,
                },
            )

        return data

    # ---------------------------------------------
    # TOP PERFORMING COURSES
    # ---------------------------------------------
    def get_top_performing_courses(self):
        Course = apps.get_model("harvest_lms", "Course")

        courses = (
            Course.objects.filter(status="published")
            .annotate(
                enrollment_count=Count("enrollment"),
                total_revenue=Sum("enrollment__price"),
                avg_rating=Avg("reviews__rating"),
            )
            .order_by("-total_revenue")[:10]
        )

        results = []

        for c in courses:
            instructor = c.author
            instructor_name = (
                f"{instructor.full_name} " if instructor.full_name else instructor.email.split("@")[0]
                
            )

            results.append(
                {
                    "id": c.id,
                    "course_title": c.title,
                    "instructor": instructor_name,
                    "enrollment": c.enrollment_count or 0,
                    "revenue": float(c.total_revenue or 0),
                    "rating": round(float(c.avg_rating or 0), 2),
                }
            )

        return results

    def calculate_growth(self, current, previous):
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)


class AdminStatisticsDetailView(APIView):
    """
    Detailed statistics for individual metrics
    GET: Returns detailed breakdown of a specific statistic
    """
    permission_classes = [IsAdminOrSuperuser]
    
    def get(self, request, metric):
        """
        Get detailed stats for specific metric
        metric can be: students, instructors, courses, revenue, rating
        """
        period = request.query_params.get('period', 'week')
        
        if metric == 'students':
            data = self.get_student_details(period)
        elif metric == 'instructors':
            data = self.get_instructor_details(period)
        elif metric == 'courses':
            data = self.get_course_details(period)
        elif metric == 'revenue':
            data = self.get_revenue_details(period)
        elif metric == 'rating':
            data = self.get_rating_details(period)
        else:
            return Response(
                {'error': 'Invalid metric. Choose from: students, instructors, courses, revenue, rating'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(data, status=status.HTTP_200_OK)
    
    def get_student_details(self, period):
        """Get detailed student statistics"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7 if period == 'week' else (30 if period == 'month' else 365))
        
        total_students = User.objects.filter(role='student').count()
        active_students = User.objects.filter(
            role='student',
            last_login__gte=start_date
        ).count()
        new_students = User.objects.filter(
            role='student',
            date_joined__gte=start_date
        ).count()
        
        return {
            'total': total_students,
            'active': active_students,
            'new': new_students,
            'inactive': total_students - active_students
        }
    
    def get_instructor_details(self, period):
        """Get detailed instructor statistics"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7 if period == 'week' else (30 if period == 'month' else 365))
        
        total_instructors = User.objects.filter(
            Q(role='instructor') | Q(is_staff=True)
        ).count()
        
        active_instructors = User.objects.filter(
            Q(role='instructor') | Q(is_staff=True),
            last_login__gte=start_date
        ).count()
        
        new_instructors = User.objects.filter(
            Q(role='instructor') | Q(is_staff=True),
            date_joined__gte=start_date
        ).count()
        
        return {
            'total': total_instructors,
            'active': active_instructors,
            'new': new_instructors
        }
    
    def get_course_details(self, period):
        """Get detailed course statistics"""
        from django.apps import apps
        Course = apps.get_model('harvest_lms', 'Course')
        
        total_courses = Course.objects.count()
        published_courses = Course.objects.filter(status='published').count()
        draft_courses = Course.objects.filter(status='draft').count()
        
        return {
            'total': total_courses,
            'published': published_courses,
            'draft': draft_courses,
            'archived': total_courses - published_courses - draft_courses
        }
    
    def get_revenue_details(self, period):
        """Get detailed revenue statistics"""
        from django.apps import apps
        Enrollment = apps.get_model('harvest_lms', 'Enrollment')
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7 if period == 'week' else (30 if period == 'month' else 365))
        
        total_revenue = Enrollment.objects.aggregate(
            total=Sum('price')
        )['total'] or 0
        
        period_revenue = Enrollment.objects.filter(
            enrolled_at__gte=start_date
        ).aggregate(
            total=Sum('price')
        )['total'] or 0
        
        return {
            'total_lifetime': float(total_revenue),
            'period_revenue': float(period_revenue),
            'currency': 'USD'
        }
    
    def get_rating_details(self, period):
        """Get detailed rating statistics"""
        from django.apps import apps
        Review = apps.get_model('harvest_lms', 'Review')
        
        avg_rating = Review.objects.aggregate(avg=Avg('rating'))['avg'] or 0
        total_reviews = Review.objects.count()
        
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[f'{i}_star'] = Review.objects.filter(rating=i).count()
        
        return {
            'average_rating': round(float(avg_rating), 2),
            'total_reviews': total_reviews,
            'distribution': rating_distribution
        }
@extend_schema(
    tags=["Admin Transaction History"],
    summary="Retrieve the logged-in user's transaction history"
)
class Transactionview(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        transactions = Transaction.objects.filter(user=user).order_by('-date')
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

