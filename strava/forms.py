from typing import ClassVar

from django import forms

from strava.models import RunnerSettings


class RunnerSettingsForm(forms.ModelForm):
    """
    The enrichment toggles on the settings screen.

    Each field carries the sample line it controls, so the template can show
    what the switch actually writes to Strava without repeating the copy.
    """

    EXAMPLES: ClassVar[dict[str, str]] = {
        "weather_report": (
            "Broken clouds, 14.2°C feels like 13.1°C, Humidity 78%, Wind 18.4km/h from SW, gusting up to 31.7km/h"
        ),
        "weather_emoji": "Afternoon Run ☁",
        "triathlon_score": "tri%: 0.50",
        "animal_comparison": "This was faster than a Leaf-tailed Gecko but slower than a Humpback Whale.",
    }

    class Meta:
        model = RunnerSettings
        fields: ClassVar[list[str]] = ["weather_report", "weather_emoji", "triathlon_score", "animal_comparison"]
        labels: ClassVar[dict[str, str]] = {
            "weather_report": "Weather report",
            "weather_emoji": "Weather emoji in the title",
            "triathlon_score": "Triathlon %",
            "animal_comparison": "Animal comparison",
        }
        help_texts: ClassVar[dict[str, str]] = {
            "weather_report": "Conditions at the start point, appended to the description.",
            "weather_emoji": "A single glyph added to the activity name.",
            "triathlon_score": "How far through a full-distance leg this activity took you.",
            "animal_comparison": "Your average speed placed between two animals.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            # Unchecked boxes are simply absent from the POST, so none of these
            # can be required.
            field.required = False
            field.example = self.EXAMPLES[name]
