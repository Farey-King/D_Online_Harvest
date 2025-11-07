from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PasswordResetOTP, User, SessionLog,Profile
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

# Logic to get user profile