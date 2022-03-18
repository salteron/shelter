import uuid

from django.db import models

from shelter.wallets.models import Currencies


class TransactionStates(models.TextChoices):
    PENDING = "pending", "pending"
    SUCCEEDED = "succeeded", "succeeded"
    CANCELED = "canceled", "canceled"


class Transaction(models.Model):
    class Meta:
        abstract = True

    value = models.DecimalField(
        max_digits=19, decimal_places=4, verbose_name="Значение"
    )
    currency = models.CharField(
        choices=Currencies.choices, max_length=3, verbose_name="Валюта"
    )
    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        db_index=True,
        verbose_name="Идентификатор транзакции",
    )
    state = models.CharField(
        choices=TransactionStates.choices,
        max_length=30,
        verbose_name="Состояние транзакции",
    )
    cancelation_reason = models.TextField(
        blank=True, null=True, verbose_name="Причина отмены"
    )
    wallet = models.ForeignKey(
        "wallets.Wallet",
        on_delete=models.PROTECT,
        related_name="%(class)ss",
        verbose_name="Кошелек",
    )
    payment_system_id = models.CharField(
        max_length=100, verbose_name="Идентификатор платежной системы"
    )
    payment_system_transaction_id = models.CharField(
        max_length=100, verbose_name="Идентификатор транзакции в платежной системе"
    )


class Deposit(Transaction):
    confirmation_url = models.URLField(verbose_name="Ссылка для подтверждения")


class Payout(Transaction):
    pass
