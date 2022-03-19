import uuid

from django.contrib.auth import models as users
from django.db import transaction

from shelter.deposits import models, tasks
from shelter.payment_systems.superpay import Superpay
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


# TODO: передавать конкретную платежную систему
def create_deposit(user: users.User, amount: wallets.Amount) -> models.Deposit:
    """

    Если сначала создать депозит, то можно
    - обеспечить идемпотентность, передавая в апи deposit и используя там, например,
      deposit.transaction_id в качестве idempotency_key;
    - отложить http-запрос в фон, обеспечив скорость ответа и повторные попытки
      при ошибках сети
    - реализовать метод "попробовать снова" recreate_deposit / recreated_hold, который
      просто поставит по-новой джоб, отправляющий запрос

    Поэтому мы создаем транзакции в статусе CREATED.
    Ставим джоб, который, если транзакция все еще CREATED,  отправит запрос и затем выставит
    статус PENDING

    """

    deposit = user.deposits.create(
        value=amount.value,
        currency=amount.currency,
        state=models.TransactionStates.CREATED,
        payment_system_id="superpay",  # TODO: payment_system_id брать из переменной класса
    )

    tasks.create_payment_system_deposit_task.delay(deposit.pk)

    return deposit


@transaction.atomic
def create_payment_system_deposit(deposit_id):
    deposit = models.Deposit.objects.select_for_update().get(pk=deposit_id)

    if deposit.state != models.TransactionStates.CREATED:
        return

    # TODO: брать payment system из deposit
    payment_system_deposit = Superpay().create_deposit(deposit)

    deposit.state = models.TransactionStates.PENDING
    deposit.confirmation_url = payment_system_deposit.confirmation_url
    deposit.save()


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
            state=models.TransactionStates.CREATED,
            payment_system_id=wallet.payment_system_id,
        )

    tasks.create_payment_system_payout_task.delay(payout.pk)

    return payout


@transaction.atomic
def create_payment_system_payout(payout_id):
    payout = models.Payout.objects.select_for_update().get(pk=payout_id)

    if payout.state != models.TransactionStates.CREATED:
        return

    Superpay().create_payout(payout)

    payout.state = models.TransactionStates.PENDING
    payout.save()


# TODO: по идее здесь должен быть event
# TODO: переименовать в  handle_succeeded_deposit_event ?
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
