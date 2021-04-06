from email.mime.image import MIMEImage

from django.contrib.staticfiles import finders
from django.core.mail import EmailMultiAlternatives


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
