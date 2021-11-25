from django import forms
from django.forms import fields
from accounts.models import Profile
from .models import *

class ProfileChangeForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ['alias']
        
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['alias'].widget.attrs['class'] = "form-control"
        self.fields['alias'].widget.attrs['type'] = "text"

class RegisterEventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'start_date', 'end_date', 'detail']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = "form-control"
            
        self.fields['title'].widget.attrs['placeholder'] = "Enter Title"
        self.fields['title'].widget.attrs['type'] = "text"
        self.fields['title'].widget.attrs['aria-describedby'] = "addon-wrapping4"

        self.fields['detail'].widget.attrs['placeholder'] = "Add details"
        self.fields['detail'].widget.attrs['row'] = "6"
        self.fields['detail'].widget.attrs['aria-describedby'] = "addon-wrapping5"

        self.fields['start_date'].widget.attrs['onfocus'] = "this.type='date'"
        self.fields['start_date'].widget.attrs['onfocusout'] = "this.type='text'"
        self.fields['start_date'].widget.attrs['placeholder'] = "Start"
        self.fields['start_date'].widget.attrs['aria-describedby'] = "addon-wrapping6"
        self.fields['end_date'].widget.attrs['onfocus'] = "this.type='date'"
        self.fields['end_date'].widget.attrs['onfocusout'] = "this.type='text'"
        self.fields['end_date'].widget.attrs['placeholder'] = "End"
        self.fields['end_date'].widget.attrs['aria-describedby'] = "addon-wrapping6"

class AddTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'deadline', 'detail']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = "form-control"
            
        self.fields['title'].widget.attrs['placeholder'] = "Enter Title"
        self.fields['title'].widget.attrs['type'] = "text"
        self.fields['title'].widget.attrs['aria-describedby'] = "addon-wrapping1"
        self.fields['detail'].widget.attrs['placeholder'] = "Add details"
        self.fields['detail'].widget.attrs['row'] = "6"
        self.fields['detail'].widget.attrs['aria-describedby'] = "addon-wrapping2"
        self.fields['deadline'].widget.attrs['onfocus'] = "this.type='date'"
        self.fields['deadline'].widget.attrs['aria-describedby'] = "addon-wrapping3"