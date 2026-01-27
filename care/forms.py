from django import forms
from .models import CommunicationNote
from .models import Document

class CommunicationNoteForm(forms.ModelForm):
    class Meta:
        model = CommunicationNote
        fields = ["visit_type", "note_text", "concern_flag"]
        widgets = {
            "note_text": forms.Textarea(attrs={"rows": 6}),
        }
class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["category", "file", "description"]