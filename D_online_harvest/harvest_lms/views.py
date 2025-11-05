from datetime import timezone
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .serializers import SignupSerializer, SigninSerializer
from drf_spectacular.utils import extend_schema
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from .models import SessionLog, Signin, User 

@extend_schema(
    request=SignupSerializer,
    responses={201: SignupSerializer},
    description="Create a new user account."
)
class SignupView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
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
         # ✅ SAVE SIGNIN RECORD TO DATABASE
        Signin.objects.create(user=user, email=user.email)
        # ✅ Create session record
        SessionLog.objects.create(
            user=user,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.headers.get("User-Agent", "Unknown Device")
        )

        return Response({
            "message": "Signin successful",
            "email": user.email,            # ✅ This shows the user email
            "user_id": user.id,             # optional but useful
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)

# Signout API View
@extend_schema(
    request=None,
    responses={200: None},
    description="Signout a user by blacklisting their refresh token."
)
class SignoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            #  Update last session logout time
            last_session = request.user.sessions.last()
            if last_session:
                last_session.logout_time = timezone.now()
                last_session.save()

            return Response({"message": "Logout successful"}, status=200)
        except Exception:
            return Response({"detail": "Invalid refresh token"}, status=400)