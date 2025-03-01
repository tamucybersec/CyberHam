from backend_patcher import BackendPatcher

# from cyberham.backend import create_event


class TestCreateEvent(BackendPatcher):
    def setup_method(self):
        super().setup_method()
