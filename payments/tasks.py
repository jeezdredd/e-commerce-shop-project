import random

from celery import shared_task

from orders.models import Order

from .models import Payment

ERRORS = [
    "Платёжная система временно недоступна",
    "Недостаточно средств на счёте",
    "Банк отклонил операцию",
    "Превышен лимит операций",
]


@shared_task
def process_payment(payment_id):
    try:
        payment = Payment.objects.get(pk=payment_id)
    except Payment.DoesNotExist:
        return

    number = payment.number
    if number.isdigit() and int(number) % 2 == 0 and not number.endswith("0"):
        payment.status = Payment.STATUS_CONFIRMED
        payment.error_text = ""
        payment.save(update_fields=["status", "error_text"])
        order = payment.order
        order.status = Order.STATUS_PAID
        order.save(update_fields=["status"])
        for item in order.items.all():
            item.product.purchases_count += item.count
            item.product.save(update_fields=["purchases_count"])
    else:
        payment.status = Payment.STATUS_ERROR
        payment.error_text = random.choice(ERRORS)
        payment.save(update_fields=["status", "error_text"])
