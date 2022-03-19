from shelter.deposits import services

HTTP_RETRY_EXCEPTIONS = (TimeoutError,)  # etc


def create_payment_system_deposit_task(deposit_id):
    services.create_payment_system_deposit(deposit_id)


create_payment_system_deposit_task.delay = lambda deposit_id: None
create_payment_system_deposit_task.autoretry_for = HTTP_RETRY_EXCEPTIONS
create_payment_system_deposit_task.max_retries = 5


# возможно в джобе можно отметить, что джоб будет пытаться выполниться ограниченно число раз
# а затем фоновая штука пройдется по старым Payout в статусе PENDING (!) и вернет деньги на базу,
# предварительно переведя их в статус canceled.
def create_payment_system_payout_task(payout_id):
    services.create_payment_system_payout(payout_id)


create_payment_system_payout_task.delay = lambda payout_id: None
create_payment_system_payout_task.autoretry_for = HTTP_RETRY_EXCEPTIONS
create_payment_system_payout_task.max_retries = 5
