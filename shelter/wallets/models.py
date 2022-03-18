from decimal import Decimal
from typing import NamedTuple

from django.db import models


# TODO: to utils
class Currencies(models.TextChoices):
    USD = "USD", "United States Dollar"


# TODO: to utils
class Amount(NamedTuple):
    value: Decimal
    currency: str


class Wallet(models.Model):
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
