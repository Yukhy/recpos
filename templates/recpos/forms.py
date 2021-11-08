from django import forms
from django.contrib.auth.models import User
from accounts.models import Profile



class UserChangeForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['username','first_name', 'last_name', 'email']
        
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            field.widget.attrs['class'] = "form-control"
            field.widget.attrs['type'] = "text"
        self.fields['email'].widget.attrs['readonly'] = True

class ProfileChangeForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ['alias']
        
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['alias'].widget.attrs['class'] = "form-control"
        self.fields['alias'].widget.attrs['type'] = "text"
