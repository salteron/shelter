import uuid
from typing import NamedTuple

from django.contrib.auth import models as users
from django.db import transaction

from shelter.deposits import models
from shelter.wallets import models as wallets, services as wallets_services

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
    confirmation_url: str


# TODO: передавать конкретную платежную систему
def create_deposit(user: users.User, amount: wallets.Amount) -> models.Deposit:
    transaction_id = uuid.uuid4()

    payment_system_deposit = payment_system_create_deposit(user, amount, transaction_id)

    return user.deposits.create(
        value=amount.value,
        currency=amount.currency,
        transaction_id=transaction_id,
        state=models.TransactionStates.PENDING,
        payment_system_id="superpay",  # TODO: payment_system_id брать из переменной класса
        confirmation_url=payment_system_deposit.confirmation_url,
    )


# TODO: может, merchant_id все-таки в мету? Какие еще данные нужны?
# TODO: в payment_systems
def payment_system_create_deposit(
    user: users.User,
    amount: wallets.Amount,
    merchant_id: uuid.UUID,
) -> PaymentSystemDeposit:
    return PaymentSystemDeposit(
        confirmation_url="http://superpay.com/deposit/42/confirmation"
    )


def create_payout(wallet: wallets.Wallet, amount: wallets.Amount) -> models.Payout:
    """

    Сначала мы должны поставить средства в холд у себя и только потом выполнить запрос.
    Иначе возможна ситуация, когда запрос выполнится, средства спишутся, а у нас
    операция свалится и пользователь продолжит распоряжаться деньгами, которые ему
    уже не принадлежат.

    Выполнить в одной транзакции тоже не стоит: запрос выполнится, а коммит транзакции нет.
    Мы должны записать изменения в базу, коммит.
    И уже после этого выполнить запрос.

    Да, запрос может свалиться, но мы можем вообще поставить его в джоб и сделать там retry.

    """

    with transaction.atomic():
        wallets_services.hold_amount(wallet, amount)

        payout = wallet.payouts.create(
            value=amount.value,
            currency=amount.currency,
            state=models.TransactionStates.PENDING,
            payment_system_id=wallet.payment_system_id,
        )

    # TODO: delay с retry при HTTP ошибках; Не забыть проверить, что все еще Payout is pending.
    # возможно в джобе можно отметить, что джоб будет пытаться выполниться ограниченно число раз
    # а затем фоновая штука пройдется по старым Payout в статусе PENDING (!) и вернет деньги на базу,
    # предварительно переведя их в статус canceled.
    payment_system_create_payout(payout)

    return payout


# TODO: в payment_systems
def payment_system_create_payout(payout: models.Payout):
    pass


# TODO: по идее здесь должен быть event
@transaction.atomic
def handle_succeeded_deposit(
    transaction_id: uuid.UUID, payment_system_account_number: str
):
    deposit = models.Deposit.objects.select_for_update().get(
        transaction_id=transaction_id
    )

    if deposit.state != models.TransactionStates.PENDING:
        return  # может быть некая обработка ситуации вместо игнорирования

    wallet = wallets_services.get_or_create_wallet_for_deposit(
        deposit, payment_system_account_number
    )
    wallets_services.deposit_amount(wallet, deposit.amount)

    deposit.wallet = wallet
    deposit.state = models.TransactionStates.SUCCEEDED
    deposit.save()


@transaction.atomic
def handle_canceled_deposit(transaction_id: uuid.UUID, cancelation_reason: str):
    deposit = models.Deposit.objects.select_for_update().get(
        transaction_id=transaction_id
    )

    if deposit.state != models.TransactionStates.PENDING:
        return  # может быть некая обработка ситуации вместо игнорирования

    deposit.state = models.TransactionStates.CANCELED
    deposit.cancelation_reason = cancelation_reason
    deposit.save()


@transaction.atomic
def handle_succeeded_payout(transaction_id: uuid.UUID):
    payout = models.Payout.objects.select_for_update().get(
        transaction_id=transaction_id
    )

    if payout.state != models.TransactionStates.PENDING:
        return  # может быть некая обработка ситуации вместо игнорирования

    wallets_services.withdraw_amount(payout.wallet, payout.amount)
    payout.state = models.TransactionStates.SUCCEEDED
    payout.save()


@transaction.atomic
def handle_canceled_payout(transaction_id: uuid.UUID, cancelation_reason: str):
    payout = models.Payout.objects.select_for_update().get(
        transaction_id=transaction_id
    )

    if payout.state != models.TransactionStates.PENDING:
        return  # может быть некая обработка ситуации вместо игнорирования

    wallets_services.release_amount(payout.wallet, payout.amount)
    payout.state = models.TransactionStates.CANCELED
    payout.cancelation_reason = cancelation_reason
    payout.save()
