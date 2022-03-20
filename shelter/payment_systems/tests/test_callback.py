from decimal import Decimal
from unittest.mock import patch

import pytest

from shelter.payment_systems.models import UnverifiedEventError
from shelter.payment_systems.superpay import Superpay
from shelter.transactions import factories


@pytest.mark.django_db
def test_callback(client):
    payout = factories.PayoutFactory(
        pending=True, wallet__hold=Decimal("10"), value=Decimal("10")
    )

    response = client.post(
        "/payment-systems/superpay/callback",
        {"transaction_id": payout.transaction_id},
        content_type="application/json",
    )

    assert response.status_code == 200

    payout.refresh_from_db()
    assert payout.is_succeeded()


def test_callback_when_unknown_payment_system(client):
    response = client.post("/payment-systems/unknown-system/callback")

    assert response.status_code == 404


def raise_unverified_event_error(*args, **kwargs):
    raise UnverifiedEventError


@patch.object(Superpay, "load_event", raise_unverified_event_error)
def test_callback_when_unverified_event(client):
    response = client.post(
        "/payment-systems/superpay/callback",
    )

    assert response.status_code == 400
