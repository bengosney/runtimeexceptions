import logging

from django.contrib.auth.models import User

from strava.auth import StravaOAuth
from strava.models import Runner

logger = logging.getLogger(__name__)


class ConnectStravaAccount:
    """
    Turns an OAuth callback code into a signed-in user.

    Strava owns the identity, so both the user and the runner are upserted
    from what comes back rather than merged with anything we already hold.
    """

    code: str

    def __init__(self, code: str):
        self.code = code

    def __call__(self) -> User:
        authorization = StravaOAuth().exchange_code(self.code)
        athlete = authorization.athlete

        logger.info("Connecting Strava athlete: %d", athlete.id)

        user, _ = User.objects.update_or_create(
            username=athlete.username,
            defaults={
                "first_name": athlete.firstname,
                "last_name": athlete.lastname,
            },
        )
        user.set_unusable_password()
        user.save()

        Runner.objects.update_or_create(
            strava_id=athlete.id,
            defaults={
                "access_token": authorization.access_token,
                "access_expires": authorization.expires_at,
                "refresh_token": authorization.refresh_token,
                "user": user,
            },
        )

        return user
