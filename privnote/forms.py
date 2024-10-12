from django import forms
from .models import Note

class NoteForm(forms.ModelForm):
    DURATION_CHOICES = [
        #(0, 'No expiration'),
        (10, '10 Minutes'),
        (30, '30 Minutes'),
        (60, '1 Hour'),
        (480, '8 Hours'),
        (1440, '1 Day'),
        (10080, '1 Week')
    ]
    
    duration = forms.ChoiceField(required=False, choices=DURATION_CHOICES, label="Duration")
    one_time_view = forms.BooleanField(required=False, label="One-time view only")
    
    class Meta:
        model = Note
        fields = ['content', 'duration', 'one_time_view']
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': 'Write your secret note here...'}),
        }
