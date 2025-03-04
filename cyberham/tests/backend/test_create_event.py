from copy import deepcopy
from backend_patcher import BackendPatcher
from cyberham.backend import create_event
from cyberham.tests.models import valid_event


class TestCreateEvent(BackendPatcher):
    def setup_method(self):
        super().setup_method()

    def test_create_event(self):
        event = deepcopy(valid_event)

        code = create_event(
            event["name"], event["points"], event["date"], event["resources"]
        )
        assert code is not None

        created_event = self.eventsdb.get(code)
        assert created_event is not None

        assert created_event["name"] == event["name"]
        assert created_event["points"] == event["points"]
        assert created_event["date"] == event["date"]
        assert created_event["resources"] == event["resources"]
        assert created_event["attended_users"] == [], "Nobody attended the event yet"

    def test_no_collision(self):
        event = deepcopy(valid_event)

        created: dict[str, None] = {}
        for i in range(100_000):
            code = create_event(
                event["name"], event["points"], event["date"], event["resources"]
            )
            assert (
                code not in created
            ), f"Collision detected on iteration {i} code {code}"
            created[code] = None

        assert True
