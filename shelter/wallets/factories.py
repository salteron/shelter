from decimal import Decimal

import factory

from shelter.wallets import models


class WalletFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Wallet

    deposit = Decimal("0")
    hold = Decimal("0")
    currency = models.Currencies.USD
