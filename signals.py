from django.db.models.signals import pre_save
from django.dispatch import receiver
from courier.models import CourierOrder
from order.models import Order


@receiver(pre_save, sender=Order)
def update_order_signal(sender, instance, created, **kwargs):
    if created:
        CourierOrder.objects.create(order=instance)


