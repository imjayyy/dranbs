from django import forms
from django.utils import timezone

from backend.models import Ticket


class UploadFileForm(forms.Form):
    file = forms.ImageField()


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = '__all__'

    def save(self, commit=True):
        instance = super(TicketForm, self).save(commit=False)
        if instance.pk:
            instance.replied_at = timezone.now()
        if commit:
            instance.save()
        return instance
