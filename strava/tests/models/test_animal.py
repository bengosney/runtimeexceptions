import pytest
from model_bakery import baker

from strava.models import Animal


@pytest.mark.django_db
def test_animal_str_method():
    animal = baker.make(Animal, name="tortoise", avg_speed=0.3, max_speed=0.5)

    assert str(animal) == "tortoise - 0.3"
