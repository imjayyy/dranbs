from email.mime.image import MIMEImage

from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.core.mail import EmailMultiAlternatives
from rest_framework.response import Response


def background_image():
    with open(finders.find('images/back.png'), 'rb') as f:
        logo_image = f.read()
    logo = MIMEImage(logo_image)
    logo.add_header('Content-ID', '<bg>')
    return logo


def send_email_with_background(subject, message, to_email, from_email=None, **kwargs):
    mail = EmailMultiAlternatives(subject=subject, body=message, from_email=from_email, to=[to_email], **kwargs)
    mail.mixed_subtype = 'related'
    mail.attach_alternative(message, 'text/html')
    mail.attach(background_image())

    return mail.send()


def api_auth(user, token):
    return Response({
        'meta': {
            'token': token.key
        },
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'last_name': user.last_name,
            'first_name': user.first_name,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'last_login': user.last_login,
        }
    })


def make_username(first_name, last_name):
    first_name = first_name.lower()
    last_name = last_name.lower()
    initial_username = "{}.{}".format(first_name, last_name)
    same_username_count = User.objects.filter(username=initial_username).count()
    if same_username_count > 0:
        username = "{}.{}".format(initial_username, same_username_count)
    else:
        username = initial_username
    return username
