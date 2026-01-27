from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
import json
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from .forms import CommunicationNoteForm
from .models import CommunicationNote, ServiceUser, StaffProfile
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .models import Document
from .forms import DocumentForm

def visible_service_users(user):
    """Staff see only assigned service users. Admin/Manager see all."""
    if user.is_superuser:
        return ServiceUser.objects.all()

    try:
        profile = StaffProfile.objects.get(user=user)
    except StaffProfile.DoesNotExist:
        return ServiceUser.objects.none()

    if profile.role in ("ADMIN", "MANAGER"):
        return ServiceUser.objects.all()

    return profile.assigned_service_users.all()


@login_required
def serviceuser_list(request):
    qs = visible_service_users(request.user).order_by("full_name")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(full_name__icontains=q)
    return render(request, "care/serviceuser_list.html", {"service_users": qs, "q": q})

@login_required
def serviceuser_detail(request, pk):
    su = get_object_or_404(ServiceUser, pk=pk)
    if su not in visible_service_users(request.user):
        return HttpResponse("Forbidden", status=403)

    notes = CommunicationNote.objects.filter(service_user=su)[:100]
    return render(request, "care/serviceuser_detail.html", {"su": su, "notes": notes})


@login_required
def add_note(request, pk):
    su = get_object_or_404(ServiceUser, pk=pk)
    if su not in visible_service_users(request.user):
        return HttpResponse("Forbidden", status=403)

    if request.method == "POST":
        form = CommunicationNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.service_user = su
            note.created_by = request.user
            note.client_uid = request.POST.get("client_uid", "")
            note.save()
            return redirect("care:serviceuser_detail", pk=su.pk)
    else:
        form = CommunicationNoteForm()

    return render(request, "care/note_form.html", {"su": su, "form": form})




@login_required
def export_notes_pdf(request, pk):
    su = get_object_or_404(ServiceUser, pk=pk)
    if su not in visible_service_users(request.user):
        return HttpResponse("Forbidden", status=403)

    start = request.GET.get("start")
    end = request.GET.get("end")

    qs = CommunicationNote.objects.filter(service_user=su)
    if start:
        qs = qs.filter(created_at__date__gte=start)
    if end:
        qs = qs.filter(created_at__date__lte=end)

    notes = qs.order_by("created_at")

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Raynet Care Limited - Communication Notes")
    y -= 20

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Service User: {su.full_name}")
    y -= 15
    c.drawString(40, y, f"Period: {start or 'All'} to {end or 'All'}")
    y -= 25

    c.setFont("Helvetica", 10)

    def wrap(text, max_chars=110):
        words = (text or "").split()
        lines, line = [], ""
        for w in words:
            test = (line + " " + w).strip()
            if len(test) <= max_chars:
                line = test
            else:
                lines.append(line)
                line = w
        if line:
            lines.append(line)
        return lines

    for n in notes:
        if y < 80:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)

        header = f"{n.created_at:%Y-%m-%d %H:%M} | {n.created_by.username} | {n.visit_type or '-'} | Concern: {'YES' if n.concern_flag else 'NO'}"
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, header)
        y -= 14

        c.setFont("Helvetica", 10)
        for line in wrap(n.note_text):
            if y < 80:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 10)
            c.drawString(40, y, line)
            y -= 12
        y -= 10

    c.setFont("Helvetica", 9)
    c.drawString(40, 50, "Confidential - for care delivery and compliance use only.")
    c.save()

    pdf = buffer.getvalue()
    buffer.close()

    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{su.full_name}-notes.pdf"'
    return resp
@login_required
@require_POST
def sync_push_notes(request):
    """
    Receives offline notes from localStorage and saves them.
    Payload: { "notes": [ {client_uid, service_user_id, visit_type, note_text, concern_flag}, ... ] }
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
        notes = data.get("notes", [])
    except Exception:
        return JsonResponse({"saved": 0, "errors": ["Invalid JSON"]}, status=400)

    saved = 0
    errors = []

    # Build a set of service users this user is allowed to write to
    allowed = set(visible_service_users(request.user).values_list("id", flat=True))

    for idx, n in enumerate(notes):
        try:
            service_user_id = int(n.get("service_user_id"))
            if service_user_id not in allowed:
                errors.append(f"Note {idx}: forbidden service user")
                continue

            client_uid = (n.get("client_uid") or "").strip()
            if client_uid and CommunicationNote.objects.filter(client_uid=client_uid).exists():
                # already synced earlier
                continue

            CommunicationNote.objects.create(
                service_user_id=service_user_id,
                created_by=request.user,
                visit_type=(n.get("visit_type") or "").strip(),
                note_text=(n.get("note_text") or "").strip(),
                concern_flag=bool(n.get("concern_flag")),
                client_uid=client_uid,
            )
            saved += 1
        except Exception as e:
            errors.append(f"Note {idx}: {str(e)}")

    return JsonResponse({"saved": saved, "errors": errors})
@login_required
def documents_list(request, pk):
    su = get_object_or_404(ServiceUser, pk=pk)
    if su not in visible_service_users(request.user):
        return HttpResponse("Forbidden", status=403)

    docs = Document.objects.filter(service_user=su).order_by("-uploaded_at")
    return render(request, "care/documents_list.html", {"su": su, "docs": docs})


@login_required
def document_upload(request, pk):
    su = get_object_or_404(ServiceUser, pk=pk)
    if su not in visible_service_users(request.user):
        return HttpResponse("Forbidden", status=403)

    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.service_user = su
            doc.uploaded_by = request.user
            doc.save()
            return redirect("care:documents_list", pk=su.pk)
    else:
        form = DocumentForm()

    return render(request, "care/document_upload.html", {"su": su, "form": form})