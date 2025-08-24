import argparse
import csv
import os
from statistics import mean

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from strava.models import Animal


def clean_speed(speed_string: str) -> float:
    try:
        return round(mean(map(float, speed_string.split("-"))), 2)
    except (ValueError, AttributeError):
        return 0.0


class Command(BaseCommand):
    """
    A Django management command to import data from a CSV file into the Animal model.

    This command expects a CSV file with headers that match the model's field names.
    It will create or update instances of Animal based on a unique identifier.
    """

    help = "Imports data from a CSV file into the Animal model."

    def add_arguments(self, parser: argparse.ArgumentParser):
        """
        Adds command-line arguments to the command parser.

        Args:
            parser: The command-line argument parser.
        """
        parser.add_argument("csv_file", type=str, help="The path to the CSV file to import.")

    def handle(self, *args, **options):
        """
        The main logic for the management command.

        This method reads the specified CSV file, iterates through the rows,
        and creates or updates model instances based on the data.
        """
        csv_file_path = options["csv_file"]

        if not os.path.exists(csv_file_path):
            raise CommandError(f"The specified CSV file was not found: {csv_file_path}")

        self.stdout.write(f"Starting data import from {csv_file_path}...")

        try:
            with open(csv_file_path, encoding="utf-8") as file:
                reader = csv.DictReader(file)

                with transaction.atomic():
                    for row in reader:
                        try:
                            name = row.get("Animal").strip()
                            avg_speed = clean_speed(row.get("Average Speed (km/h)", 0))
                            max_speed = clean_speed(row.get("Top Speed (km/h)", 0))
                            max_speed = max(avg_speed, max_speed)

                            if not name:
                                self.stderr.write(self.style.WARNING(f'Missing "Animal" field: {row}'))
                                continue

                            if avg_speed <= 0:
                                Animal.objects.filter(name=name).delete()
                                continue

                            obj, created = Animal.objects.get_or_create(
                                name=name,
                                defaults={
                                    "avg_speed": avg_speed,
                                    "max_speed": max_speed,
                                },
                            )

                            if created:
                                self.stdout.write(self.style.SUCCESS(f"Successfully created new item: {obj.name}"))
                            else:
                                obj.avg_speed = avg_speed
                                obj.max_speed = max_speed
                                obj.save()
                                self.stdout.write(self.style.SUCCESS(f"Successfully updated existing item: {obj.name}"))

                        except Exception as e:
                            self.stderr.write(self.style.ERROR(f"Error processing row {row}: {e}"))
                            raise CommandError("Import failed. See above for details.") from e

        except FileNotFoundError:
            raise CommandError(f"The file at {csv_file_path} does not exist.")
        except Exception as e:
            raise CommandError(f"An unexpected error occurred: {e}") from e

        self.stdout.write(self.style.SUCCESS("Data import completed successfully!"))
