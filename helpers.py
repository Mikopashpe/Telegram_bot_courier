from order.models import Order
from asgiref.sync import sync_to_async
from courier.models import CourierInfo, CourierOrder
from django.db.models import Q


@sync_to_async
def search_courier_for_orders(chat_id):
    courier_obj = CourierInfo.objects.filter(telegram=chat_id).first()
    return dict(
        location_id=courier_obj.location
    )


@sync_to_async
def un_allowed_orders_list(location_id):
    return [
        dict(
            restaurant_name=order.order.restaurant.name,
            street=order.order.street,
            house=order.order.house,
            uuid=str(order.order.uuid),
            amount=str(order.order.order_amount),
            entrance=order.order.entrance,
            intercom=order.order.intercom,
            floor=order.order.floor,
            flat=order.order.flat,
            contact_name=order.order.contact_name,
            contact_phone=order.order.contact_phone,
            order_note=order.order.order_note
        ) for order in
        CourierOrder.objects.prefetch_related('order', 'courier').filter(
            Q(order__order_status__in=['created', 'accepted', 'prepared']) &
            Q(order__order_type='delivery') &
            Q(accepted_by_courier=0) &
            Q(order__restaurant__location_id=location_id)
        ).exclude(
            order__order_status__in=['canceled']).all()

    ]


@sync_to_async
def search_courier_by_phone(phone):
    """
    Данная функция проверяет наличие отправленного курьером в телефона в базе данных, а также проверяет статус
    активности, который присваивает менеджер курьеров, тем самым разрешая или органичивая доступ к пользованию ботом.
    """
    if '+' in phone:
        remove_plus_phone = phone[1:]
        courier_activity_status = CourierInfo.objects.filter(phone_number=remove_plus_phone).first()
        if courier_activity_status.activity_status == True:
            if '+' in phone:
                searched_phone_number = phone[1:]
                info = CourierInfo.objects.filter(phone_number=searched_phone_number).first()
                if info:
                    info.phone_number = '+' + info.phone_number
                    return dict(
                        phone=info.phone_number,
                    )
                if not info:
                    return dict(
                        phone=0
                    )
    if not '+' in phone:
        info = CourierInfo.objects.filter(Q(phone_number=phone) & Q(activity_status=True)).first()
        if info:
            return dict(
                phone=info.phone_number,
            )
        if not info:
            return dict(
                phone=0
            )
    else:
        return dict(
            phone=0
        )


@sync_to_async
def writing_telegram_id(ct, chat_id):
    """
    Данная функция записывает id чата с курьером, прошедшим проверку.
    """
    if '+' in ct:
        remove_plus_phone = ct[1:]
        telegram_contact_id = CourierInfo.objects.filter(phone_number=remove_plus_phone).first()
        telegram_contact_id.telegram = chat_id
        telegram_contact_id.save()
    else:
        telegram_contact_id = CourierInfo.objects.filter(phone_number=ct).first()
        telegram_contact_id.telegram = chat_id
        telegram_contact_id.save()


@sync_to_async
def change_courier_order_status():
    """
    Данная функция мняет статус заказа на True в разделе "Курьеры - Задачи", тем самым закрывая доступ к заказу для
    других курьеров.
    """
    uuid_order = CourierOrder.objects.filter(order_id=id).get()
    uuid_order.accepted_by_courier = True
    return uuid_order


@sync_to_async
def delivered_order_change_status(uuid):
    """
    Данная функция меняет статус заказа на 'delivered'. Означает, что курьер доставил и передал заказ заказчику.
    """
    order_status_change = Order.objects.filter(uuid=uuid).get()
    order_status_change.order_status = 'delivered'
    order_status_change.save()


@sync_to_async
def search_courier_by_telegram_id(telegram_id):
    """
    Данная функция меняет статус курьера при открытии смены, делая его доступным для рассылки.
    """
    telegram_contact_id = CourierInfo.objects.filter(telegram=telegram_id).first()
    if telegram_contact_id.telegram == str(telegram_id):
        telegram_contact_id.status = True
        telegram_contact_id.save()


@sync_to_async
def search_courier_by_telegram_id_(telegram_id):
    """
    Данная функция меняет статус курьера при закрытии смены, делая его недоступным для рассылки.
    """
    telegram_contact_id = CourierInfo.objects.filter(telegram=telegram_id).first()
    if telegram_contact_id.telegram == str(telegram_id):
        telegram_contact_id.status = False
        telegram_contact_id.save()


@sync_to_async
def on_delivery_by_telegram_id(telegram_id):
    """
    Данная функция меняет статус взявшего заказ курьера, делая его недоступным для рассылки на период доставки.
    """
    telegram_contact_id = CourierInfo.objects.filter(telegram=telegram_id).first()
    if telegram_contact_id.telegram == str(telegram_id):
        telegram_contact_id.status_now = True
        telegram_contact_id.save()


@sync_to_async
def end_delivery_by_telegram_id_(telegram_id):
    """
    Данная функция меняет статус курьера после доставки заказа заказчику для дальнейшего получения рассылки.
    """
    telegram_contact_id = CourierInfo.objects.filter(telegram=telegram_id).first()
    if telegram_contact_id.telegram == str(telegram_id):
        telegram_contact_id.status_now = False
        telegram_contact_id.save()
