from decimal import Decimal

import factory
from django.contrib.auth import models as users

from shelter import money
from shelter.wallets import models


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = users.User

    username = factory.Sequence(lambda n: "user-%d" % n)


class WalletFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Wallet

    user = factory.SubFactory(UserFactory)
    payment_system_id = "superpay"
    payment_system_account_number = "superpay-007"
    deposit = Decimal("0")
    hold = Decimal("0")
    currency = money.Currencies.USD
