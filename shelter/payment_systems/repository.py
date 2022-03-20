from typing import Dict, Type

from shelter.payment_systems.models import PaymentSystem
from shelter.payment_systems.superpay import Superpay

PAYMENT_SYSTEM_BY_ID: Dict[str, Type[PaymentSystem]] = {"superpay": Superpay}
