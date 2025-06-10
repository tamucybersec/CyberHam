from backend_patcher import BackendPatcher
from cyberham.backend.events import create_event
from cyberham.tests.models import valid_event
from cyberham.database.typeddb import eventsdb


class TestCreateEvent(BackendPatcher):
    def setup_method(self):
        super().setup_method()

    def test_create_event(self):
        event = valid_event()

        code, err = create_event(event["name"], event["points"], event["date"])
        assert err == ""
        assert code is not None

        created_event = eventsdb.get([code])
        assert created_event is not None

        assert created_event["name"] == event["name"]
        assert created_event["points"] == event["points"]
        assert created_event["date"] == event["date"]

    def test_no_collision(self):
        event = valid_event()

        created: dict[str, None] = {}
        for i in range(100_000):
            code, err = create_event(event["name"], event["points"], event["date"])
            assert err == ""
            assert (
                code not in created
            ), f"Collision detected on iteration {i} code {code}"
            created[code] = None

        assert True
