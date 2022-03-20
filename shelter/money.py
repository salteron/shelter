from decimal import Decimal
from typing import NamedTuple

from django.db import models


class Currencies(models.TextChoices):
    USD = "USD", "United States Dollar"


class Amount(NamedTuple):
    value: Decimal
    currency: str
