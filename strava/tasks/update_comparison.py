import logging

from django_tasks import task

from strava.commands import UpdateComparison
from strava.models import Runner

logger = logging.getLogger(__name__)


@task
def update_comparison(runner_id: int, activity_id: int):
    logger.info("Updating comparison for runner: %d, activity: %d", runner_id, activity_id)
    runner = Runner.objects.get(id=runner_id)
    assert isinstance(runner, Runner)

    update_comparison = UpdateComparison(runner, activity_id)
    update_comparison()
