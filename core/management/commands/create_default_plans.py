"""Management command: seed the default subscription plans.

Usage:
    python manage.py create_default_plans

Safe to run multiple times (idempotent).
"""

from django.core.management.base import BaseCommand

from core.models import SubscriptionPlan

PLANS = [
    {
        "name": "free",
        "display_name": "Free",
        "price_monthly": "0.00",
        "storage_limit_mb": 5120,
        "features": [
            "Document vault (5 GB)",
            "Support tickets",
            "Security logs",
        ],
    },
    {
        "name": "pro",
        "display_name": "Pro",
        "price_monthly": "199.00",
        "storage_limit_mb": 51200,
        "features": [
            "Document vault (50 GB)",
            "Priority support",
            "Security logs",
            "ABHA integration",
            "Appointment management",
        ],
    },
    {
        "name": "elite",
        "display_name": "Elite Concierge",
        "price_monthly": "499.00",
        "storage_limit_mb": 204800,
        "features": [
            "Document vault (200 GB)",
            "Dedicated support agent",
            "Security logs",
            "ABHA integration",
            "Appointment management",
            "Ayushman eligibility checks",
        ],
    },
]


class Command(BaseCommand):
    help = "Seed default subscription plans (idempotent)."

    def handle(self, *args, **kwargs):
        for data in PLANS:
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=data["name"],
                defaults={
                    "display_name": data["display_name"],
                    "price_monthly": data["price_monthly"],
                    "storage_limit_mb": data["storage_limit_mb"],
                    "features": data["features"],
                },
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"  {verb}: {plan.display_name}"))

        self.stdout.write(self.style.SUCCESS("Default plans ready."))
