import uuid
from typing import NamedTuple

from shelter.deposits import models
from shelter.wallets import models as wallets


class PaymentSystemDeposit(NamedTuple):
    id: str
    confirmation_url: str


# TODO: передавать конкретную платежную систему
def create_deposit(wallet: wallets.Wallet, amount: wallets.Amount) -> models.Deposit:
    transaction_id = uuid.uuid4()

    payment_system_deposit = payment_system_create_deposit(
        wallet, amount, transaction_id
    )

    return models.Deposit.objects.create(
        value=amount.value,
        currency=amount.currency,
        transaction_id=transaction_id,
        state=models.TransactionStates.PENDING,
        wallet=wallet,
        payment_system_id="superpay",  # TODO: payment_system_slug брать из переменной класса
        payment_system_transaction_id=payment_system_deposit.id,
        confirmation_url=payment_system_deposit.confirmation_url,
    )


# TODO: может, merchant_id все-таки в мету? Какие еще данные нужны?
def payment_system_create_deposit(
    wallet: wallets.Wallet,
    amount: wallets.Amount,
    merchant_id: uuid.UUID,
) -> PaymentSystemDeposit:
    id = 42

    return PaymentSystemDeposit(
        id=id, confirmation_url=f"http://superpay.com/deposit/{id}/confirmation"
    )
