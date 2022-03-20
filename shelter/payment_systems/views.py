from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from shelter.payment_systems import models, repository, services


@csrf_exempt
@require_http_methods(["POST"])
def payment_system_callback_view(request, payment_system_id: str):
    if payment_system_id not in repository.PAYMENT_SYSTEM_BY_ID:
        return HttpResponseNotFound()

    try:
        services.handle_event(request, payment_system_id)
    except models.UnverifiedEventError:
        return HttpResponseBadRequest()

    return HttpResponse()
