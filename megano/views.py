from django.views.generic import TemplateView

from orders.models import Order


class PaymentPageView(TemplateView):
    def get_template_names(self):
        order = Order.objects.filter(pk=self.kwargs.get("id")).first()
        if order and order.payment_type == Order.PAYMENT_SOMEONE:
            return ["frontend/paymentsomeone.html"]
        return ["frontend/payment.html"]
