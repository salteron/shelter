from decimal import Decimal
from typing import NamedTuple

from django.contrib.auth.models import User
from django.db import models


# TODO: to utils
class Currencies(models.TextChoices):
    USD = "USD", "United States Dollar"


# TODO: to utils
class Amount(NamedTuple):
    value: Decimal
    currency: str


class Wallet(models.Model):
    # TODO: uniq index (user_id, payment_system_id, payment_system_account_number)

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="wallets",
        verbose_name="Владелец",
    )
    payment_system_id = models.CharField(
        max_length=100, verbose_name="Идентификатор платежной системы"
    )
    payment_system_account_number = models.CharField(
        max_length=100, verbose_name="Номер счета в платежной системе"
    )
    deposit = models.DecimalField(
        max_digits=19, decimal_places=4, verbose_name="Депозит"
    )
    hold = models.DecimalField(max_digits=19, decimal_places=4, verbose_name="Холд")
    currency = models.CharField(
        choices=Currencies.choices, max_length=3, verbose_name="Валюта"
    )

    @property
    def deposit_amount(self) -> Amount:
        return Amount(value=self.deposit, currency=self.currency)

    @property
    def hold_amount(self) -> Amount:
        return Amount(value=self.hold, currency=self.currency)
