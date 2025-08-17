import logging

from django_tasks import task

from strava.commands import UpdateTriathlonScore
from strava.models import Runner

logger = logging.getLogger(__name__)


@task
def update_triathlon_score(runner_id: int, activity_id: int):
    runner = Runner.objects.get(id=runner_id)
    assert isinstance(runner, Runner)

    update_triathlon_score = UpdateTriathlonScore(runner, activity_id)
    update_triathlon_score()
