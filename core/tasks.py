"""
Celery tasks for the core app.

These tasks allow expensive side effects (email notifications, push notifications,
external integrations, etc.) to run asynchronously without blocking API responses.
"""
from __future__ import annotations

import logging
from typing import Optional

from celery import shared_task
from django.apps import apps
from django.db import transaction

from core.email_service import EmailService
from core.notification_service import NotificationService

logger = logging.getLogger(__name__)


def _get_order(order_id: int):
    """Retrieve an order with related data optimized for notification tasks."""
    Order = apps.get_model("core", "Order")
    return (
        Order.objects.select_related(
            "client__user",
            "collaborator__user",
            "service",
            "status",
        )
        .filter(pk=order_id)
        .first()
    )


def _get_collaborator(collaborator_id: int):
    """Retrieve collaborator with related user."""
    Collaborator = apps.get_model("core", "Collaborator")
    return (
        Collaborator.objects.select_related("user").filter(pk=collaborator_id).first()
    )


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_order_assignment_email_task(order_id: int, collaborator_id: int) -> bool:
    """
    Send order assignment email asynchronously.

    Retries automatically on transient errors.
    """
    order = _get_order(order_id)
    collaborator = _get_collaborator(collaborator_id)

    if not order or not collaborator:
        logger.warning(
            "Order assignment email skipped because order (%s) or collaborator (%s) "
            "could not be resolved.",
            order_id,
            collaborator_id,
        )
        return False

    return EmailService.send_order_assignment_email(order, collaborator)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def create_collaborator_assignment_notification_task(
    order_id: int, collaborator_id: Optional[int], old_collaborator_id: Optional[int]
) -> Optional[int]:
    """
    Create collaborator assignment notification asynchronously.

    Returns the notification ID if created.
    """
    if not collaborator_id:
        return None

    order = _get_order(order_id)
    collaborator = _get_collaborator(collaborator_id)

    if not order or not collaborator:
        logger.warning(
            "Collaborator assignment notification skipped because order (%s) or "
            "collaborator (%s) could not be resolved.",
            order_id,
            collaborator_id,
        )
        return None

    if old_collaborator_id and old_collaborator_id == collaborator_id:
        logger.info(
            "Skipping assignment notification because collaborator did not change "
            "for order %s.",
            order_id,
        )
        return None

    notification = NotificationService.create_notification(
        user=collaborator.user,
        notification_type="order_assigned",
        title=f"New Order Assigned - Order #{order.id}",
        message=(
            f"You have been assigned a new order #{order.id} for "
            f"{order.service.name} by "
            f"{order.client.user.get_full_name() or order.client.user.username}"
        ),
        priority="medium",
        order=order,
        send_email=False,
    )

    if notification:
        logger.info(
            "Collaborator assignment notification created (id=%s) for order %s",
            notification.id,
            order.id,
        )
        return notification.id

    return None


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def create_admin_order_assignment_notification_task(order_id: int) -> Optional[int]:
    """
    Create notification for all active admins when an order is assigned.

    Returns the updated notification count or None on failure.
    """
    Admin = apps.get_model("core", "Admin")
    User = apps.get_model("core", "User")

    order = _get_order(order_id)
    if not order:
        logger.warning(
            "Admin assignment notification skipped because order (%s) "
            "could not be resolved.",
            order_id,
        )
        return None

    admin_ids = (
        Admin.objects.select_related("user")
        .filter(user__is_active=True)
        .values_list("user_id", flat=True)
    )

    if not admin_ids:
        logger.info("No active admins found for order assignment notifications.")
        return None

    notifications_created = 0
    for user_id in admin_ids:
        user = User.objects.filter(pk=user_id).first()
        if not user:
            continue

        notification = NotificationService.create_notification(
            user=user,
            notification_type="order_assigned",
            title=f"Order #{order.id} Assigned",
            message=(
                f"Order #{order.id} for {order.service.name} has been assigned to "
                f"{order.collaborator.user.get_full_name() or order.collaborator.user.username}"
                if order.collaborator and order.collaborator.user
                else "Order has been unassigned."
            ),
            priority="medium",
            order=order,
            send_email=False,
        )
        if notification:
            notifications_created += 1

    logger.info(
        "Created %s admin notifications for order assignment of order %s",
        notifications_created,
        order.id,
    )
    return notifications_created or None


@shared_task(bind=True)
def run_in_transaction(self, func_path: str, *args, **kwargs):
    """
    Execute a callable within a database transaction.

    Allows reusing complex domain logic from Celery while still benefiting from
    atomic operations.
    """
    from django.utils.module_loading import import_string

    func = import_string(func_path)

    with transaction.atomic():
        return func(*args, **kwargs)

