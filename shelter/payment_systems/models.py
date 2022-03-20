import uuid
from abc import ABCMeta, abstractmethod, abstractproperty
from typing import NamedTuple

from django.http import HttpRequest


class PaymentSystemDeposit(NamedTuple):
    confirmation_url: str


class PaymentSystemEvent:
    event_type: str

    def __init__(self, transaction_id: uuid.UUID) -> None:
        self.transaction_id = transaction_id


class DepositSucceededEvent(PaymentSystemEvent):
    event_type = "deposit_succeeded_event"

    def __init__(self, transaction_id: uuid.UUID, account_number: str) -> None:
        super().__init__(transaction_id)
        self.account_number = account_number


class DepositCanceledEvent(PaymentSystemEvent):
    event_type = "deposit_canceled_event"

    def __init__(self, transaction_id: uuid.UUID, cancelation_reason: str) -> None:
        super().__init__(transaction_id)
        self.cancelation_reason = cancelation_reason


class PayoutSucceededEvent(PaymentSystemEvent):
    event_type = "payout_succeeded_event"


class PayoutCanceledEvent(PaymentSystemEvent):
    event_type = "payout_canceled_event"

    def __init__(self, transaction_id: uuid.UUID, cancelation_reason: str) -> None:
        super().__init__(transaction_id)
        self.cancelation_reason = cancelation_reason


class UnverifiedEventError(Exception):
    pass


class PaymentSystem(metaclass=ABCMeta):
    @abstractproperty
    def id(self):
        pass

    @abstractmethod
    def create_deposit(self, deposit) -> PaymentSystemDeposit:
        pass

    @abstractmethod
    def create_payout(self, payout):
        pass

    @abstractmethod
    def load_event(self, request: HttpRequest) -> PaymentSystemEvent:
        pass
