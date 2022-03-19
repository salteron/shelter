from celery import task

from shelter.deposits import models, services

HTTP_RETRY_EXCEPTIONS = (TimeoutError,)  # etc


@task(autoretry_for=HTTP_RETRY_EXCEPTIONS, max_retries=5)
def create_payment_system_deposit_task(deposit_id):
    deposit = models.Deposit.objects.get(pk=deposit_id)
    services.create_payment_system_deposit(deposit)


# возможно в джобе можно отметить, что джоб будет пытаться выполниться ограниченно число раз
# а затем фоновая штука пройдется по старым Payout в статусе PENDING (!) и вернет деньги на базу,
# предварительно переведя их в статус canceled.
@task(autoretry_for=HTTP_RETRY_EXCEPTIONS, max_retries=5)
def create_payment_system_payout_task(payout_id):
    payout = models.Payout.objects.get(pk=payout_id)
    services.create_payment_system_payout(payout)
