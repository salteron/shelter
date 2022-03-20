from django.http import HttpRequest

from shelter.deposits import services as deposits_services
from shelter.payment_systems.repository import PAYMENT_SYSTEM_BY_ID


def handle_event(request: HttpRequest, payment_system_id: str):
    payment_system = PAYMENT_SYSTEM_BY_ID[payment_system_id]
    event = payment_system.load_event(request)

    if event.event_type == "deposit_succeeded_event":
        deposits_services.handle_deposit_succeeded_event(event)
    elif event.event_type == "deposit_canceled_event":
        deposits_services.handle_deposit_canceled_event(event)
    elif event.event_type == "payout_succeeded_event":
        deposits_services.handle_payout_succeeded_event(event)
    elif event.event_type == "payout_canceled_event":
        deposits_services.handle_payout_canceled_event(event)
