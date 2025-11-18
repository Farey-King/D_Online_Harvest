from django.urls import include, path,re_path



from  harvest_lms.views import (CompleteLessonView, CompletedListView, ConfirmPasswordResetView, InstructorCourseCreateView, InstructorCourseDeleteView, InstructorCourseDetailView, InstructorCourseEditView, InstructorCoursePerformanceView, InstructorCoursesListView, InstructorDashboardCardsView, InstructorEarningsView, MarkNotificationAsReadView, NotificationListView,
                    RequestPasswordResetView, 
                    SigninView, SignoutView, 
                    SignupView,ProfileUpdateView, UpcomingTasksView, 
                    UserLookupView,
                    StudentDashboardView,
                    CourseListView,
                    CourseDetailView,
                    EnrollInCourseView,
                    AssignmentListCreateView,
                    AssignmentDetailView,
                    UpcomingEventListView,
                    # OverdueListView,
                    # CompletedListView,
                    StudentCompletedDashboardView,
                    StudentOverdueDashboardView,
                    )
try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
except Exception:
    # drf-spectacular is not installed or import could not be resolved; provide simple fallback views
    from django.http import HttpResponse
    from django.views import View

    class _UnavailableView(View):
        def get(self, request, *args, **kwargs):
            return HttpResponse(
                "drf-spectacular is not installed. Install drf-spectacular to enable schema endpoints.",
                status=501,
            )

    SpectacularAPIView = _UnavailableView
    SpectacularSwaggerView = _UnavailableView
    SpectacularRedocView = _UnavailableView

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("signin/", SigninView.as_view(), name="signin"),
    path("signout/", SignoutView.as_view(), name="signout"),
    path("request-password-reset/", RequestPasswordResetView.as_view(), name="request-password-reset"),
    path("confirm-password-reset/", ConfirmPasswordResetView.as_view(), name="confirm-password-reset"),
    path("profile/update/", ProfileUpdateView.as_view(), name="profile"),
    path("get-user",UserLookupView.as_view(),name="get-user"),
    path("student-dashboard/",StudentDashboardView.as_view(),name="student-dashboard"),
    path("courses/", CourseListView.as_view()),
    path("courses/<int:course_id>/", CourseDetailView.as_view()),
    path("courses/<int:course_id>/enroll/", EnrollInCourseView.as_view()),
    path("lessons/<int:lesson_id>/complete/", CompleteLessonView.as_view()),
    #  Assignments
    path("student/assignments/", AssignmentListCreateView.as_view(), name="assignments"),
    path("student/assignments/<int:pk>/", AssignmentDetailView.as_view(), name="assignment-detail"),

    #  Upcoming Events
    path("student/upcoming-events/", UpcomingEventListView.as_view(), name="upcoming-events"),

    #  Overdue
    # path("api/student/overdue/", OverdueListView.as_view(), name="overdue-list"),
    path('student/overdue/dashboard/', StudentOverdueDashboardView.as_view(), name='student-overdue-dashboard'),

    #  Completed
    # path("api/student/completed/", CompletedListView.as_view(), name="completed-list"),
    path('student/completed/dashboard/', StudentCompletedDashboardView.as_view(), name='student-completed-dashboard'),
    # Instructor Dashboard Cards
    path('instructor/dashboard-cards/', InstructorDashboardCardsView.as_view(), name='instructor-dashboard-cards'),
    # Instructor Course Performance
    path('instructor/course-performance/', InstructorCoursePerformanceView.as_view(), name='instructor-course-performance'),
    path("instructor/upcoming-tasks/", UpcomingTasksView.as_view(), name="upcoming-tasks"),
    path("instructor/notifications/", NotificationListView.as_view(), name="notifications"),
    path("instructor/notification/<int:pk>/read/", MarkNotificationAsReadView.as_view(), name="mark-notification-read"),
    path("instructor/earnings-summary/", InstructorEarningsView.as_view(), name="instructor-earnings-summary"),
    path("instructor/courses/create/", InstructorCourseCreateView.as_view(), name="course-create"),
    path("instructor/courses/", InstructorCoursesListView.as_view(), name="instructor-courses"),
    path("instructor/course/<int:pk>/", InstructorCourseDetailView.as_view(), name="course-detail"),
    path("instructor/course/<int:pk>/edit/", InstructorCourseEditView.as_view(), name="course-edit"),
    path("instructor/course/<int:pk>/delete/", InstructorCourseDeleteView.as_view(), name="course-delete"),
    
]

urlpatterns += [
      # OpenAPI Schema
    path('schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
    path('swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # ReDoc UI (Optional)
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]