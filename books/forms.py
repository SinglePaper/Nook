from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from taggit.forms import TagField
from .models import Book, Review

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ('title', 'author', 'isbn', 'cover_image', 'description', 'tags')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),            
            'author': forms.TextInput(attrs={
                'class': 'author-input',
                'placeholder': 'Search for an author',
                'list': 'author-suggestions',
                'autocomplete': 'off'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'tagify-input',
                'placeholder': 'Add tags and press enter',
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # print(','.join(self.instance.tags.values_list('name', flat=True)))
            self.fields['tags'].initial = ', '.join(
                self.instance.tags.values_list('name', flat=True)
            )

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('rating', 'text')
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'rating': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
        }

class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Check if username is taken by another user
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This username is already taken.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email is taken by another user
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

class UserPasswordChangeForm(PasswordChangeForm):
    pass
