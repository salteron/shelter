import uuid
from typing import NamedTuple

from shelter.deposits import models
from shelter.wallets import models as wallets

"""
    TODO:

    В силу:
    1) > the withdrawal request includes the method, currency, and account number used
       > by the Client upon depositing monies into a Personal Account
    2) Юзер при выводе средств указывает на нашем сайте wallet, к которому привязан
       wallet_id в SuperPay, и amount.

    я делаю вывод, что кошелек - это способ пополнения и их ровно столько, сколько разных связок
    <payment-system, account-number>.

    Значит, при создании депозита мы оставляем поле кошелька пустым, вместо кошелька передаем
    пользователя и идентификатор платежной системы. Когда платежная система вернет success, то
    только тогда мы сможем создать wallet, потому что только из success мы получим данные о
    номере кошелька, использованного для пополнения. Здесь же желательно привязать кошелек к
    Deposit.

    В кошелек надо включить payment_system_id и payment_system_account_number.

    Поскольку кошелек однозначно определяет платежную систему, то в create_payout
    достаточно передать wallet и amount.

    Пока можно реализовать простой способ:
    - получения PaymentSystem по payment_system_id
    - создания кошелька, указав что надо защититься от конкурентного создания
"""


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


# TODO: передавать конкретную платежную систему
def create_payout(wallet: wallets.Wallet, amount: wallets.Amount) -> models.Payout:
    transaction_id = uuid.uuid4()

    payment_system_payout = payment_system_create_payout(wallet, amount, transaction_id)

    return models.Deposit.objects.create(
        value=amount.value,
        currency=amount.currency,
        transaction_id=transaction_id,
        state=models.TransactionStates.PENDING,
        wallet=wallet,
        payment_system_id="superpay",  # TODO: payment_system_slug брать из переменной класса
        payment_system_transaction_id=payment_system_payout.id,
    )


def payment_system_create_payout(
    wallet: wallets.Wallet,
    amount: wallets.Amount,
    merchant_id: uuid.UUID,
) -> PaymentSystemDeposit:
    id = 42

    return PaymentSystemDeposit(
        id=id, confirmation_url=f"http://superpay.com/deposit/{id}/confirmation"
    )
