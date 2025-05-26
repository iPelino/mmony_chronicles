from django import forms
from .models import XMLFile

class XMLUploadForm(forms.ModelForm):
    class Meta:
        model = XMLFile
        fields = ['file']
        labels = {
            'file': 'Upload XML File',
        }
        help_texts = {
            'file': 'Upload an XML file containing mobile money transaction data.',
        }
