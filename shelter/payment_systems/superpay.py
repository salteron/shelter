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
            **self._authorization_header,
            **{"X-Idempotency-Key": payout.transaction_id},
        }
        post(f"{settings.SUPERPAY_API_URL}/payout", headers, json)

    def load_event(self, request: HttpRequest) -> models.PaymentSystemEvent:
        if not self._verify_event_data(request):
            raise models.UnverifiedEventError

        request_body = json.loads(request.body)

        """

            В конечной реализации формирует событие нужного типа в зависимости от
            тела запроса

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

        Метод убеждается в подлинности события, в том, что оно пришло от Superpay.

        Перед тем как сформировать event Superpay:
        - формирует сообщение, являющееся производной от содержимого тела ответа
        и служебных данных
        - вычисляет хэш-сумму от сообщения (SHA-256)
        - шифрует хэш-сумму своим приватным ключом (RSA)
        - указывает полученное значение в заголовке X-Superpay-Signature

        Данный метод:
        - дешифрует значение X-Superpay-Signature при помощи публичного ключа Superpay
          (RSA)
        - формирует сообщение, являющееся производной от содержимого тела ответа и
          служебных данных
        - вычисляет хэш-сумму от сообщения (SHA-256)
        - сравнивает хэш-сумму с дешифрованным значением
        - успешное сравнение символизирует подллиность события

        """
        return True


def post(url, headers, json):
    """stub"""
    pass


def base64encode(value: str) -> str:
    """stub"""
    return value
