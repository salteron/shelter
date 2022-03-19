import uuid
from abc import ABCMeta, abstractmethod
from typing import NamedTuple


class PaymentSystemDeposit(NamedTuple):
    confirmation_url: str


class PaymentSystemEvent(NamedTuple):
    transaction_id: uuid.UUID
    event_type: str


class DepositSucceededEvent(PaymentSystemEvent):
    account_number: str
    event_type = "deposit_succeeded_event"


class DepositCanceledEvent(PaymentSystemEvent):
    cancelation_reason: str
    event_type = "deposit_canceled_event"


class PayoutSucceededEvent(PaymentSystemEvent):
    event_type = "payout_succeeded_event"


class PayoutCanceledEvent(PaymentSystemEvent):
    cancelation_reason: str
    event_type = "payout_canceled_event"


class UnverifiedEventError(Exception):
    pass


class PaymentSystem(metaclass=ABCMeta):
    @abstractmethod
    def create_deposit(self) -> PaymentSystemDeposit:
        pass

    @abstractmethod
    def create_payout(self):
        pass

    @abstractmethod
    def load_event(self, event_data: any) -> PaymentSystemEvent:
        pass
