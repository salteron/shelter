from typing import Type

from django.contrib.auth import models as users
from django.db import transaction

from shelter.payment_systems import models as payment_systems
from shelter.transactions import models, tasks
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

    if not deposit.is_created():
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

    if not payout.is_created():
        return

    payout.payment_system().create_payout(payout)

    payout.state = models.TransactionStates.PENDING
    payout.save()


@transaction.atomic
def handle_deposit_succeeded_event(event: payment_systems.DepositSucceededEvent):
    deposit = models.Deposit.objects.select_for_update().get(
        transaction_id=event.transaction_id
    )

    if not deposit.is_pending():
        return  # может быть некая обработка ситуации вместо игнорирования

    wallet = wallets_services.get_or_create_wallet_for_deposit(
        deposit, event.account_number
    )
    wallets_services.deposit_amount(wallet, deposit.amount)

    deposit.wallet = wallet
    deposit.state = models.TransactionStates.SUCCEEDED
    deposit.save()


@transaction.atomic
def handle_deposit_canceled_event(event: payment_systems.DepositCanceledEvent):
    deposit = models.Deposit.objects.select_for_update().get(
        transaction_id=event.transaction_id
    )

    if not deposit.is_pending():
        return  # может быть некая обработка ситуации вместо игнорирования

    deposit.state = models.TransactionStates.CANCELED
    deposit.cancelation_reason = event.cancelation_reason
    deposit.save()


@transaction.atomic
def handle_payout_succeeded_event(event: payment_systems.PayoutSucceededEvent):
    payout = models.Payout.objects.select_for_update().get(
        transaction_id=event.transaction_id
    )

    if not payout.is_pending():
        return  # может быть некая обработка ситуации вместо игнорирования

    wallets_services.withdraw_amount(payout.wallet, payout.amount)
    payout.state = models.TransactionStates.SUCCEEDED
    payout.save()


@transaction.atomic
def handle_payout_canceled_event(event: payment_systems.PayoutCanceledEvent):
    payout = models.Payout.objects.select_for_update().get(
        transaction_id=event.transaction_id
    )

    if not payout.is_pending():
        return  # может быть некая обработка ситуации вместо игнорирования

    wallets_services.release_amount(payout.wallet, payout.amount)
    payout.state = models.TransactionStates.CANCELED
    payout.cancelation_reason = event.cancelation_reason
    payout.save()
