from django.conf import settings
from django.utils import translation

from shelter.payment_systems import models


class Superpay(models.PaymentSystem):
    id = "superpay"

    def create_deposit(self, deposit) -> models.PaymentSystemDeposit:
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

        """

            В конечной реализации confirmation_url берется из ответа от АПИ.

        """
        return models.PaymentSystemDeposit(
            confirmation_url="http://superpay.com/deposit/42/confirmation"
        )

    def create_payout(self, payout):
        json = {
            "amount": payout.value,
            "currency": payout.currency,
            "locale": translation.get_language(),
            "wallet_id": payout.wallet.payment_system_account_number,
            "merchant_id": payout.transaction_id,
        }
        headers = {
            **self.authorization_header,
            **{"X-Idempotency-Key": payout.transaction_id},
        }
        post(f"{settings.SUPERPAY_API_URL}/payout", headers, json)

    def load_event(self, event_data: dict) -> models.PaymentSystemEvent:
        return models.PayoutSucceededEvent()

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
