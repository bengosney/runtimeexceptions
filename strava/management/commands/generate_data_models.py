import re
from collections import defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError, CommandParser

import requests
import yaml
from datamodel_code_generator import (
    DataModelType,
    LiteralType,
    PythonVersion,
    generate,
)


class Command(BaseCommand):
    help = "Fetches the Strava API swagger spec and generates Pydantic V2 models from it."

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "output_file",
            type=str,
            help="The path for the generated Python model file (e.g., 'strava_models.py').",
        )

    def get_external_schema_components(self, partial_schema):
        """
        Recursively searches and retrieves external schema components
        by following `$ref` keys. This method is called by `load_schema`.
        """
        if isinstance(partial_schema, list):
            for item in partial_schema:
                self.get_external_schema_components(item)
        elif isinstance(partial_schema, dict):
            for key, value in partial_schema.items():
                if isinstance(value, dict | list):
                    self.get_external_schema_components(value)
                elif key == "$ref":
                    if not (match := re.match(r".*#/(\w+)$", value)):
                        continue
                    schema_class = match.group(1)

                    partial_schema[key] = f"#/components/schemas/{schema_class}"

                    if value.startswith("https://") and schema_class not in self.schema_cache:
                        response = requests.get(value)
                        response.raise_for_status()

                        file_schema_classes = response.json()
                        self.schema_cache.update(file_schema_classes)
                        self.stdout.write(f"  - Fetched external schema for: {', '.join(file_schema_classes.keys())}")

    def load_schema(self):
        """
        Loads all external schemas into the main API dictionary by modifying
        `self.api_dict` and `self.schema_cache`.
        """
        self.stdout.write("Starting recursive schema loading...")
        self.get_external_schema_components(self.api_dict)

        existing_classes = new_classes = set(self.schema_cache.keys())
        while new_classes:
            for class_name in new_classes:
                self.get_external_schema_components(self.schema_cache[class_name])
            new_classes = set(self.schema_cache.keys()) - existing_classes
            existing_classes = set(self.schema_cache.keys())

    def handle(self, *args, **options):
        output_file = options["output_file"]
        output_path = Path(output_file)

        self.api_dict = defaultdict(dict)
        self.schema_cache = {}

        self.stdout.write("Fetching and converting Strava swagger.json to YAML...")
        try:
            strava_yaml_req = requests.get(
                url="https://converter.swagger.io/api/convert",
                params={"url": "https://developers.strava.com/swagger/swagger.json"},
                headers={"Accept": "application/yaml"},
            )
            strava_yaml_req.raise_for_status()
            self.api_dict = yaml.safe_load(strava_yaml_req.content)
            self.stdout.write(self.style.SUCCESS("✓ Schema fetched and converted successfully."))
        except requests.RequestException as e:
            raise CommandError(f"Failed to fetch or convert schema: {e}")

        self.load_schema()

        self.api_dict["components"]["schemas"] = self.schema_cache

        self.stdout.write("Generating Pydantic models with datamodel-code-generator...")
        try:
            generate(
                yaml.dump(self.api_dict),
                output=output_path,
                target_python_version=PythonVersion.PY_313,
                use_union_operator=True,
                enum_field_as_literal=LiteralType.All,
                use_double_quotes=True,
                field_constraints=True,
                output_model_type=DataModelType.PydanticV2BaseModel,
            )
            self.stdout.write(self.style.SUCCESS(f"\n✓ Successfully generated models at: {output_path}"))
        except Exception as e:
            raise CommandError(f"An error occurred during model generation: {e}")
