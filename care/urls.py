from django.urls import path
from . import views

app_name = "care"

urlpatterns = [
    path("service-users/", views.serviceuser_list, name="serviceuser_list"),
    path("service-users/<int:pk>/", views.serviceuser_detail, name="serviceuser_detail"),
    path("service-users/<int:pk>/notes/add/", views.add_note, name="add_note"),
    path("service-users/<int:pk>/notes/export/", views.export_notes_pdf, name="export_notes_pdf"),
    path("sync/push-notes/", views.sync_push_notes, name="sync_push_notes"),
    path("service-users/<int:pk>/documents/", views.documents_list, name="documents_list"),
    path("service-users/<int:pk>/documents/upload/", views.document_upload, name="document_upload"),
]