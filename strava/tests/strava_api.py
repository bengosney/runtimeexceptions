"""
Strava as the tests see it.

The URLs and payloads here are written out literally on purpose. They pin what
Strava actually serves, so a change to our url building, our data models or our
token handling has to answer to this file rather than be silently agreed with
by a mock of our own code.
"""

from typing import Any

API_ROOT = "https://www.strava.com/api/v3"

ATHLETE_ID = 12345
ACTIVITY_ID = 101
ACTIVITY_DISTANCE_M = 5000.0

# Decodes to three points; the rendered route is asserted on in the view tests.
POLYLINE = "_piFps|U_ulLnnqC_mqNvxq`@"

# A single point, which is too short a route to draw.
POINT_POLYLINE = "_riyH~oR"


def strava_url(path: str) -> str:
    return f"{API_ROOT}/{path}"


ATHLETE: dict[str, Any] = {
    "id": ATHLETE_ID,
    "username": "testrunner",
    "firstname": "Test",
    "lastname": "Runner",
    "resource_state": 2,
    "city": "London",
    "country": "United Kingdom",
}

TOKENS: dict[str, Any] = {
    "token_type": "Bearer",
    "access_token": "new_access_token",
    "expires_at": 2000000000,
    "expires_in": 21600,
    "refresh_token": "new_refresh_token",
}

AUTHORIZATION: dict[str, Any] = TOKENS | {"athlete": ATHLETE}


def activity(**overrides: Any) -> dict[str, Any]:
    """
    A 5km run, in the shape Strava sends it.

    5km of the 10km run leg is a triathlon score of 50%, and 2.78 m/s is
    10 kph, which the animal comparison sits either side of.
    """
    return {
        "id": ACTIVITY_ID,
        "name": "Morning Run",
        "description": "",
        "type": "Run",
        "sport_type": "Run",
        "distance": ACTIVITY_DISTANCE_M,
        "moving_time": 1800,
        "elapsed_time": 1900,
        "average_speed": 2.78,
        "start_date": "2026-01-01T08:00:00Z",
        "start_latlng": [51.5, -0.1],
        "end_latlng": [51.51, -0.12],
        "map": {"id": "a101", "polyline": POLYLINE, "summary_polyline": POLYLINE},
    } | overrides
