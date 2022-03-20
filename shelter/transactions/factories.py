import uuid
from decimal import Decimal

import factory

from shelter import money
from shelter.transactions import models
from shelter.wallets.factories import UserFactory, WalletFactory


class DepositFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Deposit

    user = factory.SubFactory(UserFactory)

    class Params:
        created = factory.Trait(
            state=models.TransactionStates.CREATED, wallet=None, confirmation_url=None
        )
        pending = factory.Trait(
            state=models.TransactionStates.PENDING,
            wallet=None,
            confirmation_url="http://superpay.com/deposit/42/confirmation",
        )
        canceled = factory.Trait(
            state=models.TransactionStates.CANCELED,
            wallet=None,
            confirmation_url="http://superpay.com/deposit/42/confirmation",
        )

    value = Decimal("100")
    currency = money.Currencies.USD
    transaction_id = factory.LazyFunction(uuid.uuid4)
    state = models.TransactionStates.PENDING
    payment_system_id = "superpay"


class PayoutFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Payout

    wallet = factory.SubFactory(WalletFactory)

    class Params:
        created = factory.Trait(state=models.TransactionStates.CREATED)
        pending = factory.Trait(state=models.TransactionStates.PENDING)
        canceled = factory.Trait(state=models.TransactionStates.CANCELED)

    value = Decimal("100")
    currency = money.Currencies.USD
    transaction_id = factory.LazyFunction(uuid.uuid4)
    state = models.TransactionStates.PENDING
    payment_system_id = "superpay"
