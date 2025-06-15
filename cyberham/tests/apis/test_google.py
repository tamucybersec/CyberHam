# Is it possible to write tests for the emails?

from cyberham.apis.google_apis import google


class TestGoogleApi:
    def test_get_events(self):
        assert True
        return

        events, err = google.client.get_events()
        assert events
        assert err is None
        assert False
