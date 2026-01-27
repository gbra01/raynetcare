from django.db import models

# Create your models here.
from django.contrib.auth.models import User
class ServiceUser(models.Model):
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    key_notes = models.TextField(blank=True, help_text="Allergies, risks, key info")

    def __str__(self):
        return self.full_name


class StaffProfile(models.Model):
    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("MANAGER", "Manager"),
        ("STAFF", "Staff"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="STAFF")
    assigned_service_users = models.ManyToManyField(ServiceUser, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class CommunicationNote(models.Model):
    service_user = models.ForeignKey(ServiceUser, on_delete=models.CASCADE, related_name="notes")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    visit_type = models.CharField(max_length=50, blank=True)
    note_text = models.TextField()
    concern_flag = models.BooleanField(default=False)
    client_uid = models.CharField(max_length=64, blank=True, db_index=True)

class Meta:
        ordering = ["-created_at"]

class Document(models.Model):
    CATEGORY_CHOICES = [
        ("CARE_PLAN", "Care Plan"),
        ("RISK_ASSESSMENT", "Risk Assessment"),
        ("CONSENT", "Consent"),
        ("MEDICATION", "Medication"),
        ("INCIDENT", "Incident Report"),
        ("OTHER", "Other"),
    ]

    service_user = models.ForeignKey(
        ServiceUser,
        on_delete=models.CASCADE,
        related_name="documents"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )
    file = models.FileField(
        upload_to="service_user_docs/"
    )
    description = models.CharField(
        max_length=255,
        blank=True
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.service_user.full_name} - {self.get_category_display()}"
