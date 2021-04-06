from django.conf import settings
from django.contrib.auth import password_validation, authenticate, get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from backend.models import Ticket, UserProfile, Product, Board, BoardProduct, BoardFollower
from backend.utils import send_email_with_background

UserModel = get_user_model()


class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.CharField(
        label=_("Email"),
        write_only=True
    )
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label=_("Token"),
        read_only=True
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                username=email, password=password)

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class UserSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    gender = serializers.IntegerField()
    birthday = serializers.DateField(required=False, allow_null=True, format='%Y-%m-%d')
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True
    )
    password_confirm = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    email = serializers.EmailField()

    def update(self, instance, validated_data):
        instance.first_name = validated_data['first_name']
        instance.last_name = validated_data['last_name']
        instance.email = validated_data['email']
        password = validated_data.get('password', None)
        if password:
            instance.set_password(validated_data['password'])
        instance.save()
        instance.profile.gender = validated_data['gender']
        instance.profile.birthday = validated_data.get('birthday', None)
        instance.profile.save()
        return instance

    def create(self, validated_data):
        first_name = validated_data.get('first_name')
        last_name = validated_data.get('last_name')
        initial_username = "{}.{}".format(first_name, last_name)
        same_username_count = User.objects.filter(username=initial_username).count()
        if same_username_count > 0:
            username = "{}.{}".format(initial_username, same_username_count)
        else:
            username = initial_username
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        UserProfile.objects.create(
            user=user,
            gender=validated_data['gender'],
            birthday=validated_data.get('birthday', None)
        )
        return user

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
        if self.instance:
            if password:
                password_validation.validate_password(password)
        else:
            password_validation.validate_password(password)
        return password

    def validate(self, data):
        if not self.instance:
            if data['password_confirm'] != data['password']:
                raise serializers.ValidationError({
                    "password_confirm": "password doesn't match"
                })
        else:
            password = data.get('password', None)
            password_confirm = data.get('password_confirm', None)
            if password:
                if password_confirm != password:
                    raise serializers.ValidationError({
                        "password_confirm": "password doesn't match"
                    })
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, email):
        try:
            self.user = User.objects.get(email=email)
            return email
        except User.DoesNotExist:
            raise serializers.ValidationError("We couldn't find this email in our database.")
    
    def create(self, validated_data):
        email = validated_data.get('email')
        is_debug = settings.DEBUG
        message = render_to_string('emails/forgot_password.html', {
            'url': 'http://localhost:3000' if is_debug else 'https://dranbs.com',
            'uid': urlsafe_base64_encode(force_bytes(self.user.pk)),
            'token': default_token_generator.make_token(self.user),
        })
        send_email_with_background(subject="Reset Password", message=message, to_email=email)
        return {
            "message": "We sent you an email please check and click the link."
        }

    def update(self, instance, validated_data):
        pass


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField()
    password_confirm = serializers.CharField()

    def validate_uid(self, uid):
        try:
            pk = urlsafe_base64_decode(uid).decode()
            self.user = UserModel._default_manager.get(pk=pk)
            return uid
        except UserModel.DoesNotExist:
            raise serializers.ValidationError("invalid uid")

    def validate_token(self, token):
        if default_token_generator.check_token(self.user, token):
            return token
        else:
            raise serializers.ValidationError("invalid token")

    def validate_password(self, password):
        if self.instance:
            if password:
                password_validation.validate_password(password)
        else:
            password_validation.validate_password(password)
        return password

    def validate(self, data):
        if not self.instance:
            if data['password_confirm'] != data['password']:
                raise serializers.ValidationError({
                    "password_confirm": "password doesn't match"
                })
        else:
            password = data.get('password', None)
            password_confirm = data.get('password_confirm', None)
            if password:
                if password_confirm != password:
                    raise serializers.ValidationError({
                        "password_confirm": "password doesn't match"
                    })
        return data

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        self.user.set_password(validated_data.get('password'))
        self.user.save()
        return {
            "message": "Success"
        }


class CreateBoardSerializer(serializers.Serializer):
    board_name = serializers.CharField()
    board_type = serializers.ChoiceField(choices=[0, 1])
    product_id = serializers.IntegerField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def validate_board_name(self, board_name):
        user = self.user
        try:
            Board.objects.get(name=board_name, user_id=user.id)
            raise serializers.ValidationError("This name already exists in your boards.")
        except Board.DoesNotExist:
            return board_name

    def validate_product_id(self, value):
        try:
            Product.objects.get(pk=value)
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("product doesn't exists.")


class FollowBoardSerializer(serializers.Serializer):
    slug = serializers.CharField()
    username = serializers.CharField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        board = Board.objects.get(slug=validated_data['slug'], user__username=validated_data['username'])
        try:
            board_follower = BoardFollower.objects.get(board_id=board.id, user_id=self.user.id)
            board_follower.delete()
            followers = BoardFollower.objects.filter(board_id=board.id).count()
            result = {
                'followers': followers,
                'is_following': False
            }
            return result
        except BoardFollower.DoesNotExist:
            BoardFollower.objects.create(board_id=board.id, user_id=self.user.id)
            followers = BoardFollower.objects.filter(board_id=board.id).count()
            result = {
                'followers': followers,
                'is_following': True
            }
            return result

    def validate_username(self, username):
        try:
            User.objects.get(username=username)
            return username
        except User.DoesNotExist:
            raise serializers.ValidationError("user doesn't exists.")

    def validate(self, data):
        try:
            Board.objects.get(slug=data['slug'], user__username=data['username'])
            return data
        except Board.DoesNotExist:
            raise serializers.ValidationError("board doesn't exists.")


class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = '__all__'


class BoardProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardProduct
        fields = ['product', 'board']


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'
