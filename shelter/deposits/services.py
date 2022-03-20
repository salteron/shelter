import uuid
from typing import Type

from django.contrib.auth import models as users
from django.db import transaction

from shelter.deposits import models, tasks
from shelter.payment_systems import models as payment_systems
from shelter.wallets import models as wallets, services as wallets_services


def create_deposit(
    user: users.User,
    payment_system: Type[payment_systems.PaymentSystem],
    amount: wallets.Amount,
) -> models.Deposit:
    deposit = user.deposits.create(
        value=amount.value,
        currency=amount.currency,
        state=models.TransactionStates.CREATED,
        payment_system_id=payment_system.id,
    )

    tasks.create_payment_system_deposit_task.delay(deposit.pk)

    return deposit


@transaction.atomic
def create_payment_system_deposit(deposit_id):
    deposit = models.Deposit.objects.select_for_update().get(pk=deposit_id)

    if deposit.state != models.TransactionStates.CREATED:
        return

    payment_system_deposit = deposit.payment_system().create_deposit(deposit)

    deposit.state = models.TransactionStates.PENDING
    deposit.confirmation_url = payment_system_deposit.confirmation_url
    deposit.save()


def create_payout(wallet: wallets.Wallet, amount: wallets.Amount) -> models.Payout:
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

    payout.payment_system().create_payout(payout)

    payout.state = models.TransactionStates.PENDING
    payout.save()


# TODO: переименовать в  handle_deposit_succeeded_event ?
@transaction.atomic
def handle_succeeded_deposit(event: payment_systems.DepositSucceededEvent):
    deposit = models.Deposit.objects.select_for_update().get(
        transaction_id=event.transaction_id
    )

    # TODO: добавить вручную методы deposit.is_pending()
    if deposit.state != models.TransactionStates.PENDING:
        return  # может быть некая обработка ситуации вместо игнорирования

    wallet = wallets_services.get_or_create_wallet_for_deposit(
        deposit, event.account_number
    )
    wallets_services.deposit_amount(wallet, deposit.amount)

    deposit.wallet = wallet
    deposit.state = models.TransactionStates.SUCCEEDED
    deposit.save()


@transaction.atomic
def handle_canceled_deposit(event: payment_systems.DepositCanceledEvent):
    deposit = models.Deposit.objects.select_for_update().get(
        transaction_id=event.transaction_id
    )

    if deposit.state != models.TransactionStates.PENDING:
        return  # может быть некая обработка ситуации вместо игнорирования

    deposit.state = models.TransactionStates.CANCELED
    deposit.cancelation_reason = event.cancelation_reason
    deposit.save()


@transaction.atomic
def handle_succeeded_payout(event: payment_systems.PayoutSucceededEvent):
    payout = models.Payout.objects.select_for_update().get(
        transaction_id=event.transaction_id
    )

    if payout.state != models.TransactionStates.PENDING:
        return  # может быть некая обработка ситуации вместо игнорирования

    wallets_services.withdraw_amount(payout.wallet, payout.amount)
    payout.state = models.TransactionStates.SUCCEEDED
    payout.save()


@transaction.atomic
def handle_canceled_payout(event: payment_systems.PayoutCanceledEvent):
    payout = models.Payout.objects.select_for_update().get(
        transaction_id=event.transaction_id
    )

    if payout.state != models.TransactionStates.PENDING:
        return  # может быть некая обработка ситуации вместо игнорирования

    wallets_services.release_amount(payout.wallet, payout.amount)
    payout.state = models.TransactionStates.CANCELED
    payout.cancelation_reason = event.cancelation_reason
    payout.save()
