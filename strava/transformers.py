import logging
from datetime import datetime

from django.utils.timezone import make_aware

from strava.data_models import EventWebhook
from strava.models import Event, Runner

logger = logging.getLogger(__name__)


def webhook_data_to_event(event_data: EventWebhook) -> Event:
    logger.debug("Transforming webhook data to event: %s", event_data)
    event_time = make_aware(datetime.fromtimestamp(event_data.event_time))
    owner = Runner.objects.get(strava_id=event_data.owner_id)
    return Event(
        object_type=event_data.object_type,
        object_id=event_data.object_id,
        aspect_type=event_data.aspect_type,
        updates=event_data.updates,
        owner=owner,
        subscription_id=event_data.subscription_id,
        event_time=event_time,
    )
