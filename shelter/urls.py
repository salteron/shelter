from django.urls import path

from shelter.payment_systems import views as payment_systems

urlpatterns = [
    path(
        "payment-systems/<slug:payment_system_id>/callback",
        payment_systems.payment_system_callback_view,
    ),
]
