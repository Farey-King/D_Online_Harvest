from django.urls import path

from .views import ConfirmPasswordResetView,RequestPasswordResetView, SigninView, SignoutView, SignupView 
# from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("signin/", SigninView.as_view(), name="signin"),
    path("signout/", SignoutView.as_view(), name="signout"),
    path("request-password-reset/", RequestPasswordResetView.as_view(), name="request-password-reset"),
    path("confirm-password-reset/", ConfirmPasswordResetView.as_view(), name="confirm-password-reset"),
]

# urlpatterns += [
#     path("schema/", SpectacularAPIView.as_view(), name="schema"),
#     path("schema/swagger-ui/", SpectacularSwaggerView.as_view(), name="swagger-ui"),
#     path("schema/redoc/", SpectacularRedocView.as_view(), name="redoc"),
# ]