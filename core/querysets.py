"""
Reusable queryset helpers for common access patterns.
"""
from __future__ import annotations

from django.apps import apps
from django.db import models


def order_with_related():
    """
    Return an ``Order`` queryset with the related objects eagerly loaded and a
    boolean flag that indicates whether livrables exist.
    """
    Order = apps.get_model("core", "Order")
    Livrable = apps.get_model("core", "Livrable")

    livrable_exists = Livrable.objects.filter(order_id=models.OuterRef("pk"))

    return Order.objects.select_related(
        "client__user",
        "service",
        "status",
        "collaborator__user",
    ).prefetch_related(
        "livrables",
    ).annotate(
        has_livrable_flag=models.Exists(livrable_exists)
    )

