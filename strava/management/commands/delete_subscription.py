from django.core.management.base import BaseCommand, CommandError

from strava.webhook import WebhookManager


class Command(BaseCommand):
    help: str = "Delete a Strava subscription"

    def add_arguments(self, parser):
        parser.add_argument("subscription_id", type=int, help="ID of the subscription to delete")

    def handle(self, *args, **options):
        subscription_id = options["subscription_id"]

        webhook_manager = WebhookManager()
        try:
            webhook_manager.delete_subscription(subscription_id)
        except Exception as e:
            raise CommandError(f"Error deleting subscription: {e}")

        self.stdout.write(self.style.SUCCESS(f"Successfully deleted subscription with ID {subscription_id}"))
