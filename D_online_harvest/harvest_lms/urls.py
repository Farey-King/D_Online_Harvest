from django.urls import include, path,re_path



from  harvest_lms.views import (AdminActivityLogView, AdminDashboardView, AdminStatisticsDetailView, AdvancedInformationView,
                                CompleteLessonView, 
                                CompletedListView,
                                ConfirmPasswordResetView, CourseCommissionView, CourseCurriculumDeleteView, CourseCurriculumUpdateView,
                                InstructorCourseCreateView,
                                InstructorCourseDeleteView,
                                InstructorCourseDetailView,
                                InstructorCourseEditView,
                                InstructorCoursePerformanceView,
                                InstructorCoursesListView,
                                InstructorDashboardCardsView,
                                InstructorEarningsView, 
                                MarkNotificationAsReadView, 
                                NotificationListView, PayPalCheckoutView, PurchaseHistoryView,
                    RequestPasswordResetView, 
                    SigninView, SignoutView, 
                    SignupView,ProfileUpdateView, SystemReportView, TransactionHistoryView, Transactionview, UpcomingTasksView, 
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
                    ConversationListView,
                    ConversationDetailView,
                    SendMessageView,
                    StartConversationView,
                    DeleteConversationView,
                    BlockConversationView,
                    BasicInformationView,
                    CourseCurriculumView,
                    PublishCourseView,
                    EarningsDashboardView,
                    NotificationView,
                    RevenueChartView,
                    CreateSystemReportView,
                    CheckoutView,
                    ShoppingCartView,
                    PayPalPaymentSuccessView,
                    )
try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView # type: ignore
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
    path("completed/", CompletedListView.as_view(), name="completed-list"),
     # Shopping Cart and Checkout
    path("shopping-cart/", ShoppingCartView.as_view(), name="shopping-cart"),
    # path('shopping-cart/<int:item_id>/', ShoppingCartView.as_view(), name='shopping-cart-delete'),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("paypal-checkout/", PayPalCheckoutView.as_view(), name="paypal-checkout"),
    path("paypal-success/", PayPalPaymentSuccessView.as_view(), name="paypal-success"),
    # Instructor Dashboard Cards
    path('instructor/dashboard-cards/', InstructorDashboardCardsView.as_view(), name='instructor-dashboard-cards'),

    path("purchase-history/", PurchaseHistoryView.as_view(), name="purchase-history"),
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
    # Conversations and Messaging
    path("messages/", ConversationListView.as_view(), name="message-list"),
    path("messages/start/", StartConversationView.as_view(), name="message-start"),
    path("messages/<int:convo_id>/", ConversationDetailView.as_view(), name="message-detail"),
    path("messages/<int:convo_id>/send/", SendMessageView.as_view(), name="message-send"),
    path("messages/<int:convo_id>/delete/", DeleteConversationView.as_view(), name="message-delete"),
    path("messages/<int:convo_id>/block/", BlockConversationView.as_view(), name="message-block"),
    path("basic-information/", BasicInformationView.as_view(), name="basic-information"),
    path("advanced-information/", AdvancedInformationView.as_view(), name="advanced-information"),
    path("course-curriculum/", CourseCurriculumView.as_view(), name="course-curriculum"),
    path("curriculum/<int:pk>/update/", CourseCurriculumUpdateView.as_view(), name="curriculum-update"),
    path("curriculum/<int:pk>/delete/", CourseCurriculumDeleteView.as_view(), name="curriculum-delete"),
    path("earnings/", EarningsDashboardView.as_view(), name="instructor-earnings"),
    path("publish-course/", PublishCourseView.as_view(), name="publish-course"),
    path("transaction-history/", TransactionHistoryView.as_view(), name="transaction-history"),
     # Admin dashboard endpoint
    path('panel/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path("panel/admin/notifications/", NotificationView.as_view(), name="admin-notifications"),
    # Detailed statistics endpoints
    path('panel/admin/statistics/<str:metric>/', AdminStatisticsDetailView.as_view(), name='admin-statistics-detail'),
    path('panel/admin/commission-table/', CourseCommissionView.as_view(), name='admin-commission-table'),
        # Revenue Chart Data endpoint  
    path('panel/admin/revenue-chart/', RevenueChartView.as_view(), name='admin-revenue-chart'), 

    path('panel/admin/transaction/', Transactionview.as_view(), name='transaction-view'),
    path('panel/admin/activity-logs/', AdminActivityLogView.as_view(), name='admin-activity-logs'),
    path('panel/admin/system-reports/', SystemReportView.as_view(), name='admin-system-reports'),
    path('panel/admin/create-system-report/', CreateSystemReportView.as_view(), name='create-system-report'),
    
]

urlpatterns += [
      # OpenAPI Schema
    path('schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
    path('swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # ReDoc UI (Optional)
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]