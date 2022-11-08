from order.models import Order
from django.db.models import Q
from courier.models import CourierOrder
from asgiref.sync import sync_to_async


@sync_to_async
def orders_list():
    list_orders = []
    for order in Order.objects.filter(Q(order_status__in=['created']) & Q(order_type='delivery')).exclude(
            order_status__in=['canceled']):
        list_orders.append(f'{order.restaurant} => {order.street}, {order.house}')
    return '\n'.join(list_orders)
