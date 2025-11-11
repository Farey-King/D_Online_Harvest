from django.urls import include, path,re_path



from  harvest_lms.views import (CompleteLessonView, ConfirmPasswordResetView,
                    RequestPasswordResetView, 
                    SigninView, SignoutView, 
                    SignupView,ProfileUpdateView, 
                    UserLookupView,
                    StudentDashboardView,
                    CourseListView,
                    CourseDetailView,
                    EnrollInCourseView
                    )
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

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
    
]

urlpatterns += [
      # OpenAPI Schema
    path('schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
    path('swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # ReDoc UI (Optional)
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]