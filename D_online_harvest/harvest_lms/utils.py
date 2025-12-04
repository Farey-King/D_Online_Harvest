from datetime import timedelta
from django.utils import timezone


def get_period_range(period):
    now = timezone.now()

    if period == "daily":
        start = now - timedelta(days=1)
        prev_start = start - timedelta(days=1)
        prev_end = start

    elif period == "weekly":
        start = now - timedelta(days=7)
        prev_start = start - timedelta(days=7)
        prev_end = start

    elif period == "monthly":
        start = now - timedelta(days=30)
        prev_start = start - timedelta(days=30)
        prev_end = start

    elif period == "yearly":
        start = now - timedelta(days=365)
        prev_start = start - timedelta(days=365)
        prev_end = start

    else:
        raise ValueError("Invalid period")

    return start, now, prev_start, prev_end
