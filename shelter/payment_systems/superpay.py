from django.conf import settings
from django.utils import translation

from shelter.deposits import models as deposits
from shelter.payment_systems import models


class Superpay(models.PaymentSystem):
    # TODO: deposit.transaction_id в качестве idempotency_key;
    def create_deposit(self, deposit: deposits.Deposit) -> models.PaymentSystemDeposit:
        json = {
            "amount": deposit.value,
            "currency": deposit.currency,
            "redirect_success_url": settings.SUPERPAY_REDIRECT_SUCCESS_URL,
            "redirect_failure_url": settings.SUPERPAY_REDIRECT_FAILURE_URL,
            "locale": translation.get_language(),
            "merchant_id": deposit.transaction_id,
        }
        headers = {
            **self.authorization_header,
            **{"X-Idempotency-Key": deposit.transaction_id},
        }
        post(f"{settings.SUPERPAY_API_URL}/deposit", headers, json)

    @property
    def authorization_header(self) -> dict:
        credentials = f"{settings.SUPERPAY_CLIENT_ID}:{settings.SUPERPAY_CLIENT_SECRET}"
        return {"Authorization": f"Basic {base64encode(credentials)}"}


def post(url, headers, json):
    """stub"""
    pass


def base64encode(value: str) -> str:
    """stub"""
    return value