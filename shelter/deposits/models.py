import uuid

from django.contrib.auth.models import User
from django.db import models

from shelter.wallets import models as wallets
from shelter.wallets.models import Currencies


class TransactionStates(models.TextChoices):
    CREATED = "created", "created"
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
    payment_system_id = models.CharField(
        max_length=100, verbose_name="Идентификатор платежной системы"
    )

    @property
    def amount(self) -> wallets.Amount:
        return wallets.Amount(value=self.value, currency=self.currency)


class Deposit(Transaction):
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="deposits",
        verbose_name="Владелец",
    )

    wallet = models.ForeignKey(
        "wallets.Wallet",
        on_delete=models.PROTECT,
        related_name="deposits",
        verbose_name="Кошелек",
        null=True,
        blank=True,
    )

    confirmation_url = models.URLField(
        null=True, blank=True, verbose_name="Ссылка для подтверждения"
    )


class Payout(Transaction):
    wallet = models.ForeignKey(
        "wallets.Wallet",
        on_delete=models.PROTECT,
        related_name="payouts",
        verbose_name="Кошелек",
    )
