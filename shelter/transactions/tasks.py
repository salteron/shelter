from shelter.transactions import services

HTTP_RETRY_EXCEPTIONS = (TimeoutError,)  # etc

"""

    Конечная реализация может использовать Celery в качестве очередей задач.

"""


def create_payment_system_deposit_task(deposit_id):
    services.create_payment_system_deposit(deposit_id)


create_payment_system_deposit_task.delay = lambda deposit_id: None
create_payment_system_deposit_task.autoretry_for = HTTP_RETRY_EXCEPTIONS
create_payment_system_deposit_task.max_retries = 5


def create_payment_system_payout_task(payout_id):
    """

    Для простоты предполагаем, что в случае ошибок задача переставляется бесчисленное
    количество раз до тех пор, пока не выполнится.

    В конечной реализации число повторных попыток должно быть ограничено, а Celery Beat
    регулярно запускает задачу, которая отыскивает payouts в статусе CREATED,
    созданные более t назад, переводит их в статус CANCELED и релизит соответствующие
    ("висящие") холды.

    """
    services.create_payment_system_payout(payout_id)


create_payment_system_payout_task.delay = lambda payout_id: None
create_payment_system_payout_task.autoretry_for = HTTP_RETRY_EXCEPTIONS
create_payment_system_payout_task.max_retries = None  # infinity
