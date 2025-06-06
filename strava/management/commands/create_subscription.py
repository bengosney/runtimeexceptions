from django.core.management.base import BaseCommand, CommandError

from strava.webhook import WebhookManager


class Command(BaseCommand):
    help = "Create a Strava subscription"

    def handle(self, *args, **options):
        webhook_manager = WebhookManager()

        for subscription in webhook_manager.list_subscriptions():
            self.stdout.write(f"Found existing subscription with callback URL: {subscription['callback_url']}")
            if subscription["callback_url"] == webhook_manager._get_full_url():
                self.stdout.write(self.style.SUCCESS("Subscription already exists"))
                return
            webhook_manager.delete_subscription(subscription["id"])

        try:
            webhook_manager.create_subscription()
        except Exception as e:
            raise CommandError(f"Error creating subscription: {e}")

        self.stdout.write(self.style.SUCCESS("Successfully created subscription"))
