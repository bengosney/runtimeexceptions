from django.core.management.base import BaseCommand, CommandError

from strava.webhook import WebhookManager


class Command(BaseCommand):
    help: str = "List Strava subscriptions"

    def handle(self, *args, **options):
        webhook_manager = WebhookManager()

        try:
            subscriptions = webhook_manager.list_subscriptions()
        except Exception as e:
            raise CommandError(f"Error listing subscriptions: {e}")

        self.stdout.write(self.style.SUCCESS("Subscriptions:"))
        for subscription in subscriptions:
            self.stdout.write(f"ID: {subscription['id']}, Callback URL: {subscription['callback_url']}")
