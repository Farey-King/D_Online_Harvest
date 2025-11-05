from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

User = get_user_model()

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "full_name", "phone_number", "password", "confirm_password"]
    
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

class sessionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone_number']
    