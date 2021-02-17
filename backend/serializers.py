from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from rest_framework import serializers

from backend.models import UserProfile


class UserInfo:
    def __init__(self, username, email, password, first_name, last_name, gender, birthday, country):
        self.username = username
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender
        self.birthday = birthday
        self.country = country


class UserSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    gender = serializers.IntegerField()
    birthday = serializers.DateField(required=False, allow_null=True)
    country = serializers.CharField(required=False, allow_null=True)
    username = serializers.CharField()
    password = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    password_confirm = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    email = serializers.EmailField()

    def update(self, instance, validated_data):
        instance.first_name = validated_data['first_name']
        instance.last_name = validated_data['last_name']
        instance.email = validated_data['email']
        instance.set_password(validated_data['password'])
        instance.save()
        instance.profile.gender = validated_data['gender']
        instance.profile.birthday = validated_data['birthday']
        instance.profile.country = validated_data['country']
        instance.profile.save()
        return instance

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        UserProfile.objects.create(
            user=user,
            gender=validated_data['gender'],
            country=validated_data['country'],
            birthday=validated_data['birthday']
        )
        return user

    def validate_username(self, username):
        if self.instance and self.instance.username == username:
            return username
        else:
            try:
                User.objects.get(username=username)
                raise serializers.ValidationError("username already taken")
            except User.DoesNotExist:
                return username

    def validate_email(self, email):
        if self.instance and self.instance.email == email:
            return email
        else:
            try:
                User.objects.get(email=email)
                raise serializers.ValidationError("email already taken")
            except User.DoesNotExist:
                return email

    def validate_password(self, password):
        if not self.instance:
            password_validation.validate_password(password)
        return password

    def validate(self, data):
        if not self.instance:
            if data['password_confirm'] != data['password']:
                raise serializers.ValidationError({
                    "password_confirm": "password doesn't match"
                })
        else:
            if data['password'] and data['password_confirm'] != data['password']:
                raise serializers.ValidationError({
                    "password_confirm": "password doesn't match"
                })
        return data
