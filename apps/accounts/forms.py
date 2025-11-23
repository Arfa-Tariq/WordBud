from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """Enhanced signup form with additional fields."""
    
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'First name (optional)'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Last name (optional)'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ("email", "username", "first_name", "last_name", "password1", "password2")
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Email address'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Username (optional)'
            }),
        }


class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form."""
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email address'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password'
        })
    )


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating user profile information.
    Handles basic info, bio, and profile image.
    """
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'bio', 'profile_image']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'profile-input',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'profile-input',
                'placeholder': 'Last name'
            }),
            'username': forms.TextInput(attrs={
                'class': 'profile-input',
                'placeholder': 'Username (optional)'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'profile-textarea',
                'placeholder': 'Tell us about yourself...',
                'rows': 4,
                'maxlength': 500
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'profile-file-input',
                'accept': 'image/jpeg,image/png,image/gif'
            })
        }
        help_texts = {
            'username': 'Optional. Letters, digits and @/./+/-/_ only.',
            'bio': 'Maximum 500 characters.',
            'profile_image': 'JPG, PNG, or GIF. Maximum 5MB.'
        }
    
    def clean_profile_image(self):
        """Validate profile image size and format."""
        image = self.cleaned_data.get('profile_image')
        
        if image:
            # Check file size (5MB max)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('Image file too large. Maximum size is 5MB.')
            
            # Check file extension
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif']
            ext = image.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise ValidationError('Invalid file format. Use JPG, PNG, or GIF.')
        
        return image
    
    def clean_bio(self):
        """Validate bio length."""
        bio = self.cleaned_data.get('bio', '')
        if len(bio) > 500:
            raise ValidationError('Bio must be 500 characters or less.')
        return bio


class PreferencesForm(forms.Form):
    """
    Form for updating user preferences.
    Handles theme, notifications, and other settings.
    """
    
    THEME_CHOICES = [
        ('light', 'Light Mode'),
        ('dark', 'Dark Mode'),
        ('auto', 'Auto (System)'),
    ]
    
    theme = forms.ChoiceField(
        choices=THEME_CHOICES,
        initial='auto',
        widget=forms.RadioSelect(attrs={
            'class': 'preference-radio'
        }),
        help_text='Choose your preferred theme'
    )
    
    email_notifications = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'preference-checkbox'
        }),
        help_text='Receive email notifications for important updates'
    )
    
    show_search_history = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'preference-checkbox'
        }),
        help_text='Save and display your search history'
    )
    
    items_per_page = forms.IntegerField(
        min_value=10,
        max_value=100,
        initial=20,
        widget=forms.NumberInput(attrs={
            'class': 'preference-input',
            'step': '10'
        }),
        help_text='Number of items to show per page (10-100)'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-populate with user's current preferences
        if user and user.preferences:
            prefs = user.preferences
            self.fields['theme'].initial = prefs.get('theme', 'auto')
            self.fields['email_notifications'].initial = prefs.get('email_notifications', True)
            self.fields['show_search_history'].initial = prefs.get('show_search_history', True)
            self.fields['items_per_page'].initial = prefs.get('items_per_page', 20)


class EmailChangeForm(forms.Form):
    """Form for changing user email address."""
    
    new_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'profile-input',
            'placeholder': 'New email address'
        }),
        help_text='Enter your new email address'
    )
    
    confirm_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'profile-input',
            'placeholder': 'Confirm new email'
        }),
        help_text='Re-enter your new email address'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'profile-input',
            'placeholder': 'Current password'
        }),
        help_text='Enter your current password to confirm'
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        new_email = cleaned_data.get('new_email')
        confirm_email = cleaned_data.get('confirm_email')
        password = cleaned_data.get('password')
        
        # Check emails match
        if new_email and confirm_email and new_email != confirm_email:
            raise ValidationError('Email addresses do not match.')
        
        # Check password is correct
        if self.user and password:
            if not self.user.check_password(password):
                raise ValidationError('Incorrect password.')
        
        # Check email is not already in use
        if new_email and CustomUser.objects.filter(email=new_email).exclude(pk=self.user.pk).exists():
            raise ValidationError('This email address is already in use.')
        
        return cleaned_data


class PasswordChangeCustomForm(forms.Form):
    """Custom password change form."""
    
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'profile-input',
            'placeholder': 'Current password'
        })
    )
    
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'profile-input',
            'placeholder': 'New password'
        }),
        help_text='At least 8 characters'
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'profile-input',
            'placeholder': 'Confirm new password'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        """Verify current password is correct."""
        password = self.cleaned_data.get('current_password')
        if self.user and not self.user.check_password(password):
            raise ValidationError('Current password is incorrect.')
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError('New passwords do not match.')
            
            if len(new_password) < 8:
                raise ValidationError('Password must be at least 8 characters long.')
        
        return cleaned_data
