from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ClearableFileInput
from django.contrib.auth.models import User
from .models import AudioFile


class AudioFileForm(forms.ModelForm):
    class Meta:
        model = AudioFile
        fields = ["name", "category", "price", "publish_date", "image", "audio_file"]
        widgets = {
            "publish_date": forms.DateInput(attrs={"type": "date"}),
            "image": ClearableFileInput(attrs={"accept": ".png,.jpg,.jpeg"}),
            "audio_file": ClearableFileInput(attrs={"accept": ".mp3"}),
        }

    def _validate_uploaded_file(self, uploaded_file, allowed_extensions, field_label):
        if not uploaded_file:
            return uploaded_file

        name = uploaded_file.name.lower()
        allowed = tuple(allowed_extensions)
        if not name.endswith(allowed):
            raise forms.ValidationError(f"{field_label} must use one of: {', '.join(allowed)}")
        return uploaded_file

    def clean_image(self):
        image = self.cleaned_data.get("image")
        return self._validate_uploaded_file(image, (".png", ".jpg", ".jpeg"), "Image")

    def clean_audio_file(self):
        audio = self.cleaned_data.get("audio_file")
        return self._validate_uploaded_file(audio, (".mp3",), "Audio file")


class FilterForm(forms.Form):
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ("publish_date", "Publish date"),
            ("name", "Name"),
            ("price", "Price"),
        ],
        widget=forms.RadioSelect,
    )
    order = forms.ChoiceField(
        required=False,
        choices=[("asc", "Ascending"), ("desc", "Descending")],
        widget=forms.HiddenInput,
    )
    categories = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple)
    min_price = forms.DecimalField(required=False, decimal_places=2, max_digits=10)
    max_price = forms.DecimalField(required=False, decimal_places=2, max_digits=10)
    start_date = forms.DateField(required=False, widget=forms.TextInput(attrs={"placeholder": "dd/mm/yyyy"}))
    end_date = forms.DateField(required=False, widget=forms.TextInput(attrs={"placeholder": "dd/mm/yyyy"}))


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(required=False, max_length=32, help_text="Optional until email verification.")
    terms_consent = forms.BooleanField(required=True, label="I agree to the Terms")
    privacy_consent = forms.BooleanField(required=True, label="I agree to the Privacy Policy")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class PhoneVerificationForm(forms.Form):
    phone_number = forms.CharField(max_length=32)
    code = forms.CharField(max_length=6, min_length=6, required=False)


