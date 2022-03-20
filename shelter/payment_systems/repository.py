import typing

from shelter.payment_systems.models import PaymentSystem
from shelter.payment_systems.superpay import Superpay

PAYMENT_SYSTEM_BY_ID: typing.Dict[str, PaymentSystem] = {"superpay": Superpay}
