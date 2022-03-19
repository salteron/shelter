import uuid
from decimal import Decimal

import factory

from shelter.deposits import models
from shelter.wallets.factories import UserFactory, WalletFactory


class DepositFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Deposit

    user = factory.SubFactory(UserFactory)

    class Params:
        pending = factory.Trait(state=models.TransactionStates.PENDING, wallet=None)

    value = Decimal("100")
    currency = models.Currencies.USD
    transaction_id = factory.LazyFunction(uuid.uuid4)
    state = models.TransactionStates.PENDING
    payment_system_id = "superpay"
    confirmation_url = "http://superpay.com/deposit/42/confirmation"


class PayoutFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Payout

    wallet = factory.SubFactory(WalletFactory)

    class Params:
        pending = factory.Trait(state=models.TransactionStates.PENDING)

    value = Decimal("100")
    currency = models.Currencies.USD
    transaction_id = factory.LazyFunction(uuid.uuid4)
    state = models.TransactionStates.PENDING
    payment_system_id = "superpay"
