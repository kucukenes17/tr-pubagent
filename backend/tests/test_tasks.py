from collections import Counter

from app.tasks import TASKS


def test_benchmark_has_eighty_unique_tasks():
    assert len(TASKS) == 80
    assert len({task.id for task in TASKS}) == 80


def test_split_is_frozen_at_24_16_40():
    assert Counter(task.split for task in TASKS) == {
        "development": 24,
        "validation": 16,
        "test": 40,
    }


def test_every_task_has_oracle_and_authorization_contract():
    for task in TASKS:
        assert task.user_request
        assert task.authorization.goal
        assert task.tags
        assert task.max_steps == 20
