from django import forms

class XMLUploadForm(forms.Form):
    xml_file = forms.FileField(
        label='Upload XML File',
        help_text='Upload an XML file containing mobile money transaction data.'
    )