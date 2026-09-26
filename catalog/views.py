import mimetypes
import hashlib
import logging
import secrets
import subprocess
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import FileResponse, Http404, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .forms import AudioFileForm, FilterForm, RegistrationForm
from .forms import PhoneVerificationForm
from .models import AudioFile, AuthAuditEvent, Purchase, VerificationChallenge, VerificationProfile
from .services import apply_filters, attach_media_urls, build_filter_form

logger = logging.getLogger(__name__)
VERIFICATION_EXPIRY = timedelta(hours=24)
PHONE_CODE_EXPIRY = timedelta(minutes=10)
MAX_CHALLENGE_ATTEMPTS = 5


def get_cart(request):
    return request.session.setdefault("cart", [])


def save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


def redirect_back_or_default(request, default_url):
    redirect_to = request.POST.get("next") or request.GET.get("next") or request.META.get("HTTP_REFERER")
    if redirect_to and url_has_allowed_host_and_scheme(redirect_to, allowed_hosts={request.get_host()}):
        return redirect(redirect_to)
    return redirect(default_url)


def audit(request, event, user=None, channel="", metadata=None):
    AuthAuditEvent.objects.create(
        user=user,
        event=event,
        channel=channel,
        ip_address=request.META.get("REMOTE_ADDR"),
        metadata=metadata or {},
    )


def token_digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def create_challenge(user, channel, value, expires_in):
    VerificationChallenge.objects.filter(
        user=user, channel=channel, consumed_at__isnull=True
    ).update(consumed_at=timezone.now())
    return VerificationChallenge.objects.create(
        user=user,
        channel=channel,
        token_hash=token_digest(value),
        expires_at=timezone.now() + expires_in,
    )


def send_email_verification(user, token):
    link = f"{settings.SITE_URL}{reverse('verify_email', args=[user.pk, token])}"
    send_mail(
        "Verify your AudioWeb email",
        f"Verify your email by opening this link:\n\n{link}\n\nThis link expires in 24 hours.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_phone_code(phone_number, code):
    logger.info("Phone verification code generated for %s", phone_number)


def health_check(request):
    return JsonResponse({"status": "ok", "database": "postgresql", "service": "audioweb"})


def archive(request):
    items = AudioFile.objects.all()
    form = build_filter_form(request, items)
    items = apply_filters(items, form)

    purchased_ids = set()
    if request.user.is_authenticated:
        purchased_ids = set(
            Purchase.objects.filter(user=request.user, status=Purchase.Status.PAID).values_list("audio_file_id", flat=True)
        )

    cart = get_cart(request)
    preview_ids = set()
    for item in items:
        item.is_purchased = item.id in purchased_ids
        item.in_cart = item.id in cart
        item.preview = not item.is_purchased
        if item.preview:
            preview_ids.add(item.id)
    attach_media_urls(items, preview_ids)

    cart_items = AudioFile.objects.filter(id__in=cart)
    active_sort = request.GET.get("sort_by") or request.GET.get("active_sort") or ""
    active_order = request.GET.get("order") or "asc"
    return render(
        request,
        "catalog/archive.html",
        {
            "items": items,
            "form": form,
            "active_sort": active_sort,
            "active_order": active_order,
            "cart_items": cart_items,
            "cart_count": len(cart),
        },
    )


@user_passes_test(lambda user: user.is_staff)
def admin_panel(request):
    items = AudioFile.objects.all()
    form = build_filter_form(request, items)
    items = apply_filters(items, form)
    attach_media_urls(items)
    active_sort = request.GET.get("sort_by") or request.GET.get("active_sort") or ""
    active_order = request.GET.get("order") or "asc"
    return render(
        request,
        "catalog/admin_panel.html",
        {"items": items, "form": form, "active_sort": active_sort, "active_order": active_order},
    )


@user_passes_test(lambda user: user.is_staff)
def upload_audio(request):
    if request.method == "POST":
        form = AudioFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect(reverse("admin_panel"))
    else:
        form = AudioFileForm()
    return render(request, "catalog/audio_form.html", {"form": form, "title": "Upload audio"})


@user_passes_test(lambda user: user.is_staff)
def edit_audio(request, pk):
    item = get_object_or_404(AudioFile, pk=pk)
    if request.method == "POST":
        form = AudioFileForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect(reverse("admin_panel"))
    else:
        form = AudioFileForm(instance=item)
    return render(request, "catalog/audio_form.html", {"form": form, "title": "Edit audio"})


@user_passes_test(lambda user: user.is_staff)
def delete_audio(request, pk):
    item = get_object_or_404(AudioFile, pk=pk)
    if request.method == "POST":
        item.delete()
        return redirect(reverse("admin_panel"))
    return render(request, "catalog/confirm_delete.html", {"item": item})


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.email = form.cleaned_data["email"]
                user.is_active = False
                user.save()
                profile = VerificationProfile.objects.create(
                    user=user,
                    phone_number=form.cleaned_data.get("phone_number", ""),
                    terms_consent_at=timezone.now(),
                    privacy_consent_at=timezone.now(),
                    consent_version=settings.CONSENT_VERSION,
                )
                token = secrets.token_urlsafe(32)
                create_challenge(user, VerificationChallenge.CHANNEL_EMAIL, token, VERIFICATION_EXPIRY)
                transaction.on_commit(lambda: send_email_verification(user, token))
            audit(request, "registration_created", user, "email", {"consent_version": profile.consent_version})
            return redirect(reverse("verification_sent"))
    else:
        form = RegistrationForm()
    return render(request, "registration/register.html", {"form": form})


def verification_sent(request):
    return render(request, "registration/verification_sent.html")


def verify_email(request, user_id, token):
    user = get_object_or_404(User, pk=user_id)
    challenge = VerificationChallenge.objects.filter(
        user=user, channel=VerificationChallenge.CHANNEL_EMAIL, consumed_at__isnull=True
    ).order_by("-created_at").first()
    valid = challenge and challenge.usable and secrets.compare_digest(challenge.token_hash, token_digest(token))
    if valid:
        challenge.consumed_at = timezone.now()
        challenge.save(update_fields=["consumed_at"])
        profile, _ = VerificationProfile.objects.get_or_create(user=user)
        profile.email_verified_at = timezone.now()
        profile.save(update_fields=["email_verified_at"])
        user.is_active = True
        user.save(update_fields=["is_active"])
        audit(request, "email_verified", user, "email")
        return redirect(reverse("login") + "?verified=1")
    audit(request, "email_verification_failed", user, "email")
    return render(request, "registration/verification_invalid.html", status=400)


@login_required
def account_overview(request):
    profile, _ = VerificationProfile.objects.get_or_create(user=request.user)
    phone_form = PhoneVerificationForm(initial={"phone_number": profile.phone_number})
    return render(request, "catalog/account.html", {"profile": profile, "phone_form": phone_form})


@login_required
@require_POST
def start_phone_verification(request):
    profile, _ = VerificationProfile.objects.get_or_create(user=request.user)
    form = PhoneVerificationForm(request.POST)
    if form.is_valid():
        phone_number = form.cleaned_data["phone_number"].strip()
        code = f"{secrets.randbelow(1000000):06d}"
        profile.phone_number = phone_number
        profile.phone_verified_at = None
        profile.save(update_fields=["phone_number", "phone_verified_at"])
        create_challenge(request.user, VerificationChallenge.CHANNEL_PHONE, code, PHONE_CODE_EXPIRY)
        send_phone_code(phone_number, code)
        audit(request, "phone_verification_sent", request.user, "phone")
    return redirect(reverse("phone_verification"))


@login_required
def phone_verification(request):
    profile, _ = VerificationProfile.objects.get_or_create(user=request.user)
    form = PhoneVerificationForm(request.POST or None, initial={"phone_number": profile.phone_number})
    if request.method == "POST" and form.is_valid():
        challenge = VerificationChallenge.objects.filter(
            user=request.user, channel=VerificationChallenge.CHANNEL_PHONE, consumed_at__isnull=True
        ).order_by("-created_at").first()
        valid = challenge and challenge.usable and challenge.attempts < MAX_CHALLENGE_ATTEMPTS
        if valid:
            challenge.attempts += 1
            valid = secrets.compare_digest(challenge.token_hash, token_digest(form.cleaned_data["code"]))
            challenge.save(update_fields=["attempts"])
        if valid:
            challenge.consumed_at = timezone.now()
            challenge.save(update_fields=["consumed_at"])
            profile.phone_verified_at = timezone.now()
            profile.save(update_fields=["phone_verified_at"])
            audit(request, "phone_verified", request.user, "phone")
            return redirect(reverse("account_overview"))
        audit(request, "phone_verification_failed", request.user, "phone")
        form.add_error("code", "The code is invalid or expired.")
    return render(request, "registration/phone_verification.html", {"form": form})


@login_required
def my_content(request):
    purchased_items = AudioFile.objects.filter(purchases__user=request.user, purchases__status=Purchase.Status.PAID).distinct()
    attach_media_urls(purchased_items)
    return render(request, "catalog/my_content.html", {"purchased_items": purchased_items})


@login_required
def checkout(request):
    cart = get_cart(request)
    if not cart:
        return redirect(reverse("archive"))
    items = list(AudioFile.objects.filter(id__in=cart))
    total = sum((item.price for item in items), Decimal("0.00"))
    return render(
        request,
        "catalog/checkout.html",
        {"items": items, "total": total, "provider": settings.PAYMENT_PROVIDER, "payment_mode": settings.PAYMENT_MODE},
    )


@login_required
@require_POST
def checkout_confirm(request):
    cart = get_cart(request)
    if not cart:
        return redirect(reverse("archive"))

    items = list(AudioFile.objects.filter(id__in=cart))
    purchases = []
    for item in items:
        purchase, _ = Purchase.objects.get_or_create(
            user=request.user,
            audio_file=item,
            defaults={"amount": item.price, "currency": settings.PAYMENT_CURRENCY, "provider": settings.PAYMENT_PROVIDER},
        )
        purchase.amount = item.price
        purchase.currency = settings.PAYMENT_CURRENCY
        purchase.provider = settings.PAYMENT_PROVIDER
        purchase.status = Purchase.Status.PAID
        purchase.provider_reference = f"demo-{secrets.token_hex(8)}"
        purchase.paid_at = timezone.now()
        purchase.save(update_fields=["amount", "currency", "provider", "provider_reference", "status", "paid_at"])
        purchases.append(purchase)

    save_cart(request, [])
    return redirect(reverse("checkout_success", args=[purchases[0].pk]))


@login_required
def checkout_success(request, purchase_id):
    purchase = get_object_or_404(
        Purchase,
        pk=purchase_id,
        user=request.user,
        status=Purchase.Status.PAID,
    )
    purchases = Purchase.objects.filter(user=request.user, status=Purchase.Status.PAID).order_by("-paid_at")
    return render(request, "catalog/checkout_success.html", {"purchase": purchase, "purchases": purchases})


def audio_stream(request, pk):
    audio = get_object_or_404(AudioFile, pk=pk)
    preview = request.GET.get("preview") == "1"
    owned = request.user.is_authenticated and Purchase.objects.filter(
        user=request.user, audio_file=audio
    ).exists()

    if not owned and not preview:
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login

            return redirect_to_login(request.get_full_path())
        raise Http404

    if not audio.audio_file:
        raise Http404

    if preview and not owned:
        process = subprocess.Popen(
            [
                settings.FFMPEG_BINARY, "-hide_banner", "-loglevel", "error", "-i",
                audio.audio_file.path, "-t", "60", "-f", "mp3", "-",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

        def preview_chunks():
            try:
                while chunk := process.stdout.read(64 * 1024):
                    yield chunk
            finally:
                process.stdout.close()
                process.wait()

        response = StreamingHttpResponse(preview_chunks(), content_type="audio/mpeg")
        response["Content-Disposition"] = "inline"
        response["Cache-Control"] = "private, no-store"
        return response

    response = FileResponse(audio.audio_file.open("rb"), content_type="audio/mpeg")
    response["Content-Disposition"] = "inline"
    response["Cache-Control"] = "private, no-store"
    return response


def image_stream(request, pk):
    audio = get_object_or_404(AudioFile, pk=pk)
    if not audio.image:
        raise Http404
    content_type = mimetypes.guess_type(audio.image.name)[0] or "application/octet-stream"
    response = FileResponse(audio.image.open("rb"), content_type=content_type)
    response["Content-Disposition"] = "inline"
    response["Cache-Control"] = "public, max-age=3600"
    return response


@require_POST
def cart_add(request, audio_id):
    audio = get_object_or_404(AudioFile, pk=audio_id)
    cart = get_cart(request)
    if audio.id not in cart:
        cart.append(audio_id)
        save_cart(request, cart)
    return redirect_back_or_default(request, reverse("archive"))


@require_POST
def cart_remove(request, audio_id):
    get_object_or_404(AudioFile, pk=audio_id)
    cart = get_cart(request)
    if audio_id in cart:
        cart.remove(audio_id)
        save_cart(request, cart)
    return redirect_back_or_default(request, reverse("archive"))


@login_required
def cart_buy(request):
    if request.method == "POST":
        return redirect(reverse("checkout"))
    return redirect(reverse("archive"))


@require_POST
def logout_view(request):
    """Simple logout that redirects to the archive page."""
    logout(request)
    return redirect(reverse("archive"))
