import json
import uuid

from django.conf import settings
from django.http import HttpRequest
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
            **self._authorization_header,
            **{"X-Idempotency-Key": deposit.transaction_id},
        }
        post(f"{settings.SUPERPAY_API_URL}/deposit", headers, json)

        """

            In the final implementation, the confirmation_url is retrieved from
            the API response.

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
            **self._authorization_header,
            **{"X-Idempotency-Key": payout.transaction_id},
        }
        post(f"{settings.SUPERPAY_API_URL}/payout", headers, json)

    def load_event(self, request: HttpRequest) -> models.PaymentSystemEvent:
        if not self._verify_event_data(request):
            raise models.UnverifiedEventError

        request_body = json.loads(request.body)

        """

            In the final implementation, it generates an event of the required
            type depending on the request body.

        """

        return models.PayoutSucceededEvent(
            transaction_id=uuid.UUID(request_body["transaction_id"])
        )

    @property
    def _authorization_header(self) -> dict:
        credentials = f"{settings.SUPERPAY_CLIENT_ID}:{settings.SUPERPAY_CLIENT_SECRET}"
        return {"Authorization": f"Basic {base64encode(credentials)}"}

    def _verify_event_data(self, request: HttpRequest) -> bool:
        """

        The method ensures the authenticity of the event, verifying that it
        originated from Superpay.

        Before forming the event Superpay:
        - Constructs a message derived from the content of the response body and auxiliary data.
        - Computes the hash value of the message (SHA-256).
        - Encrypts the hash value with its private key (RSA).
        - Specifies the obtained value in the X-Superpay-Signature header.

        This method:
        - Decrypts the value of X-Superpay-Signature using the Superpay public key (RSA).
        - Constructs a message derived from the content of the response body and auxiliary data.
        - Computes the hash value of the message (SHA-256).
        - Compares the hash value with the decrypted value.
        - A successful comparison indicates the authenticity of the event.

        """
        return True


def post(url, headers, json):
    """stub"""
    pass


def base64encode(value: str) -> str:
    """stub"""
    return value
