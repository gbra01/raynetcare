from django.contrib import admin

# Register your models here.
from .models import ServiceUser, StaffProfile, CommunicationNote

@admin.register(ServiceUser)
class ServiceUserAdmin(admin.ModelAdmin):
    list_display = ("full_name", "date_of_birth")
    search_fields = ("full_name",)

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    filter_horizontal = ("assigned_service_users",)

@admin.register(CommunicationNote)
class CommunicationNoteAdmin(admin.ModelAdmin):
    list_display = ("service_user", "created_by", "created_at", "concern_flag")
    list_filter = ("concern_flag", "created_at")
    search_fields = ("note_text",)