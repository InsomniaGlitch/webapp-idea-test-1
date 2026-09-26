from django.contrib import admin
from django.urls import include, path
from catalog import views as catalog_views

urlpatterns = [
    path("logout/", catalog_views.logout_view, name="custom_logout"),
    path("django-admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("healthz/", catalog_views.health_check, name="health_check"),
    path("", catalog_views.archive, name="home"),
    path("archive/", catalog_views.archive, name="archive"),
    path("audio/<int:pk>/stream/", catalog_views.audio_stream, name="audio_stream"),
    path("audio/<int:pk>/image/", catalog_views.image_stream, name="image_stream"),
    path("admin/", catalog_views.admin_panel, name="admin_panel"),
    path("admin/upload/", catalog_views.upload_audio, name="upload_audio"),
    path("admin/edit/<int:pk>/", catalog_views.edit_audio, name="edit_audio"),
    path("admin/delete/<int:pk>/", catalog_views.delete_audio, name="delete_audio"),
    path("account/", catalog_views.account_overview, name="account_overview"),
    path("account/content/", catalog_views.my_content, name="my_content"),
    path("register/", catalog_views.register, name="register"),
    path("verification-sent/", catalog_views.verification_sent, name="verification_sent"),
    path("verify-email/<int:user_id>/<str:token>/", catalog_views.verify_email, name="verify_email"),
    path("account/phone/", catalog_views.start_phone_verification, name="start_phone_verification"),
    path("account/phone/verify/", catalog_views.phone_verification, name="phone_verification"),
    path("cart/add/<int:audio_id>/", catalog_views.cart_add, name="cart_add"),
    path("cart/remove/<int:audio_id>/", catalog_views.cart_remove, name="cart_remove"),
    path("cart/checkout/", catalog_views.checkout, name="checkout"),
    path("cart/checkout/confirm/", catalog_views.checkout_confirm, name="checkout_confirm"),
    path("cart/checkout/success/<int:purchase_id>/", catalog_views.checkout_success, name="checkout_success"),
    path("cart/buy/", catalog_views.cart_buy, name="cart_buy"),
]

