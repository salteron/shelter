from django.contrib.auth.models import User
from django.db import models

from shelter import money


class Wallet(models.Model):
    class Meta:
        unique_together = (
            ("user_id", "payment_system_id", "payment_system_account_number"),
        )

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="wallets",
        verbose_name="Owner",
    )
    payment_system_id = models.CharField(
        max_length=100, verbose_name="Payment system ID"
    )
    payment_system_account_number = models.CharField(
        max_length=100, verbose_name="Payment system account number"
    )
    deposit = models.DecimalField(
        max_digits=19, decimal_places=4, verbose_name="Deposit"
    )
    hold = models.DecimalField(max_digits=19, decimal_places=4, verbose_name="Hold")
    currency = models.CharField(
        choices=money.Currencies.choices, max_length=3, verbose_name="Currency"
    )

    @property
    def deposit_amount(self) -> money.Amount:
        return money.Amount(value=self.deposit, currency=self.currency)

    @property
    def hold_amount(self) -> money.Amount:
        return money.Amount(value=self.hold, currency=self.currency)
