from shelter.transactions import services

HTTP_RETRY_EXCEPTIONS = (TimeoutError,)  # etc

"""

    The final implementation may utilize Celery as the task queue.

"""


def create_payment_system_deposit_task(deposit_id):
    services.create_payment_system_deposit(deposit_id)


create_payment_system_deposit_task.delay = lambda deposit_id: None
create_payment_system_deposit_task.autoretry_for = HTTP_RETRY_EXCEPTIONS
create_payment_system_deposit_task.max_retries = 5


def create_payment_system_payout_task(payout_id):
    """

    For simplicity, we assume that in case of errors, the task is retried
    indefinitely until it succeeds.

    In the final implementation, the number of retry attempts should be limited,
    and Celery Beat regularly triggers a task that identifies payouts in the
    CREATED status, created more than t time ago, cancels them, and releases the
    corresponding ("hanging") holds.

    """
    services.create_payment_system_payout(payout_id)


create_payment_system_payout_task.delay = lambda payout_id: None
create_payment_system_payout_task.autoretry_for = HTTP_RETRY_EXCEPTIONS
create_payment_system_payout_task.max_retries = None  # infinity
