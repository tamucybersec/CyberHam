import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import pytest
from cyberham.apis.dashboard import app

client = TestClient(app)

# Fixture to provide a standard payload
@pytest.fixture
def standard_user_payload():
    return {
        "user_id": "u1",
        "grad_semester": "2026S",
        "resume_filename": "",
        "resume_format": ""
    }

class TestDashboard:
    
    # ------------------------------------------------------------------
    # /login 
    # ------------------------------------------------------------------
    
    @pytest.mark.parametrize(
        "token_val, mock_return, expected_body",
        [
            ("some-token", (0, None), 0),          # none user
            ("some-token", (1, None), 1),          # sponsor user
            ("some-token", (2, None), 2),          # committee user
            ("some-token", (3, None), 3),          # admin user
            ("definitely-invalid", (0, "invalid token"), 0), # invalid token
        ]
    )
    @patch("cyberham.apis.dashboard.token_status")
    def test_login_tokens(self, mock_token_status, token_val, mock_return, expected_body):
        """
        Verifies that the /login endpoint correctly maps token validation 
        results from the database to the appropriate user permission levels.
        """
        mock_token_status.return_value = mock_return
        
        resp = client.get("/login", params={"token": token_val})
        
        assert resp.status_code == 200
        assert resp.json() == expected_body
        mock_token_status.assert_called_once_with(token_val)

    def test_login_missing_token(self):
        """
        Verifies that the API rejects login attempts that omit the token parameter entirely.
        """
        resp = client.get("/login")
        assert resp.status_code == 422

    # ------------------------------------------------------------------
    # /register
    # ------------------------------------------------------------------
    
    def test_register_missing_user_json(self):
        """
        Verifies that the API blocks registration if the user_json payload is missing.
        """
        resp = client.post("/register/test-ticket")
        assert resp.status_code == 422

    def test_register_invalid_json(self):
        """
        Verifies that the API safely catches and rejects malformed JSON strings.
        """
        resp = client.post(
            "/register/test-ticket",
            data={"user_json": "not-valid-json"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid user JSON"

    @patch("cyberham.apis.dashboard.register")
    def test_register_missing_fields(self, mock_register):
        """
        Documents a known issue: The API currently lacks validation for missing keys 
        in the JSON payload and will crash (500 Error) if required fields are missing.
        """
        mock_register.side_effect = KeyError("grad_semester")
        
        # Use a specific client just for this test that doesn't crash the runner
        safe_client = TestClient(app, raise_server_exceptions=False)

        resp = safe_client.post(
            "/register/test-ticket",
            data={"user_json": '{"user_id": "u1"}'}
        )

        assert resp.status_code == 500

    @patch("cyberham.apis.dashboard.register")
    def test_register_success_no_resume(self, mock_register, standard_user_payload):
        """
        Verifies the happy path for a user successfully registering without uploading a resume.
        """
        mock_register.return_value = ("Registered successfully", None)
        resp = client.post(
            "/register/test-ticket",
            data={"user_json": json.dumps(standard_user_payload)},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Registered successfully"
        mock_register.assert_called_once()
    
    @patch("cyberham.apis.dashboard.register")
    def test_register_returns_error(self, mock_register, standard_user_payload):
        """
        Verifies that the endpoint correctly bubbles up errors (like an invalid ticket)
        returned by the underlying database registration logic.
        """
        mock_err = MagicMock()
        mock_err.json.return_value = {"detail": "Invalid ticket"}
        mock_register.return_value = ("", mock_err)

        resp = client.post(
            "/register/test-ticket",
            data={"user_json": json.dumps(standard_user_payload)},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid ticket"

    @patch("cyberham.apis.dashboard.register")
    @patch("cyberham.apis.dashboard.upload_resume", new_callable=AsyncMock)
    def test_register_with_resume_success(self, mock_upload, mock_register, standard_user_payload):
        """
        Verifies the happy path for a user successfully registering and uploading a resume file.
        """
        mock_upload.return_value = "resume.pdf"
        mock_register.return_value = ("Registered", None)

        resp = client.post(
            "/register/test-ticket",
            data={"user_json": json.dumps(standard_user_payload)},
            files={"resume": ("resume.pdf", b"dummy content")},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Registered"
        mock_upload.assert_awaited_once()
        mock_register.assert_called_once()

    @patch("cyberham.apis.dashboard.register")
    @patch("cyberham.apis.dashboard.upload_resume", new_callable=AsyncMock)
    def test_register_resume_upload_fails(self, mock_upload, mock_register, standard_user_payload):
        """
        Verifies that if the resume upload process fails, the registration process is halted 
        and an appropriate 500 error is returned.
        """
        mock_upload.return_value = ""
        mock_register.return_value = ("SHOULD_NOT_HAPPEN", None)

        resp = client.post(
            "/register/test-ticket",
            data={"user_json": json.dumps(standard_user_payload)},
            files={"resume": ("resume.pdf", b"dummy")},
        )
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Resume upload failed"
        mock_register.assert_not_called()

    # ------------------------------------------------------------------
    # /self 
    # ------------------------------------------------------------------
    
    @patch("cyberham.apis.dashboard.registerdb.get")
    def test_get_self_invalid_ticket(self, mock_register_get):
        """
        Verifies that requesting profile data with a non-existent ticket returns a 400 error.
        """
        mock_register_get.return_value = None
        resp = client.get("/self/some-ticket")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid registration link."

    @patch("cyberham.apis.dashboard.resumesdb.get")
    @patch("cyberham.apis.dashboard.usersdb.get")
    @patch("cyberham.apis.dashboard.valid_registration_time")
    @patch("cyberham.apis.dashboard.registerdb.get")
    def test_get_self_corrupt_db(
        self,
        mock_register_get,
        mock_valid_time,
        mock_users_get,
        mock_resumes_get,
    ):
        """
        Verifies that the API raises a KeyError if the database returns a corrupted 
        registration record that is missing mandatory schema fields like 'time'.
        """
        mock_register_get.return_value = {}  # missing "time" and "user_id"
        mock_valid_time.return_value = True
        mock_users_get.return_value = None
        mock_resumes_get.return_value = None

        with pytest.raises(KeyError, match="time"):
            client.get("/self/some-ticket")

    @patch("cyberham.apis.dashboard.registerdb.get")
    @patch("cyberham.apis.dashboard.valid_registration_time")
    def test_get_self_expired_link(self, mock_valid_time, mock_register_get):
        """
        Verifies that attempting to use an expired registration ticket is rejected.
        """
        mock_register_get.return_value = {"time": 123, "user_id": "u1"}
        mock_valid_time.return_value = False

        resp = client.get("/self/some-ticket")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Registration link has expired"

    @patch("cyberham.apis.dashboard.resumesdb.get")
    @patch("cyberham.apis.dashboard.registerdb.get")
    @patch("cyberham.apis.dashboard.valid_registration_time")
    @patch("cyberham.apis.dashboard.usersdb.get")
    @patch("cyberham.apis.dashboard.pretty_semester")
    def test_get_self_user_exists_no_resume(
        self,
        mock_pretty_semester,
        mock_users_get,
        mock_valid_time,
        mock_register_get,
        mock_resume_get
    ):
        """
        Verifies the happy path for retrieving an existing user's profile data 
        when they have no resume on file.
        """
        mock_register_get.return_value = {"time": 123, "user_id": "u1"}
        mock_valid_time.return_value = True
        mock_users_get.return_value = {
            "user_id": "u1",
            "grad_semester": "2026S",
            "resume_filename": "",
        }
        mock_pretty_semester.return_value = "Spring 2026"
        mock_resume_get.return_value = None

        resp = client.get("/self/some-ticket")
        assert resp.status_code == 200
        body = resp.json()

        assert body["user"]["user_id"] == "u1"
        assert body["user"]["grad_semester"] == "Spring 2026"
        assert body["resume"] == {}
        mock_valid_time.assert_called_once_with(123)

    @patch("cyberham.apis.dashboard.resumesdb.get")
    @patch("cyberham.apis.dashboard.default_user")
    @patch("cyberham.apis.dashboard.pretty_semester")
    @patch("cyberham.apis.dashboard.usersdb.get")
    @patch("cyberham.apis.dashboard.valid_registration_time")
    @patch("cyberham.apis.dashboard.registerdb.get")
    def test_get_self_uses_default(
        self,
        mock_register_get,
        mock_valid_time,
        mock_users_get,
        mock_pretty_semester,
        mock_default_user,
        mock_resumes_get,
    ):
        """
        Verifies the fallback mechanism: If a user has a valid ticket but no existing profile 
        in the database, the API gracefully creates and returns a temporary default profile 
        rather than crashing.
        """
        mock_register_get.return_value = {"time": 123, "user_id": "u2"}
        mock_valid_time.return_value = True

        mock_users_get.return_value = None
        mock_default_user.return_value = {
            "user_id": "u2",
            "grad_semester": "2026S",
            "resume_filename": "",
        }
        mock_resumes_get.return_value = None
        mock_pretty_semester.return_value = "Spring 2026"

        resp = client.get("/self/some-ticket")
        assert resp.status_code == 200
        body = resp.json()

        assert body["resume"] == {}
        assert body["user"]["user_id"] == "u2"
        assert body["user"]["grad_semester"] == "Spring 2026"

        mock_valid_time.assert_called_once_with(123)
        mock_default_user.assert_called_once_with("u2")

    @patch("cyberham.apis.dashboard.resumesdb.get")
    @patch("cyberham.apis.dashboard.pretty_semester")
    @patch("cyberham.apis.dashboard.usersdb.get")
    @patch("cyberham.apis.dashboard.valid_registration_time")
    @patch("cyberham.apis.dashboard.registerdb.get")
    def test_get_self_ok_with_resume(
        self,
        mock_register_get,
        mock_valid_time,
        mock_users_get,
        mock_pretty_semester,
        mock_resumes_get,
    ):
        """
        Verifies the happy path for retrieving an existing user's profile data, 
        ensuring that attached resume metadata is correctly fetched and parsed.
        """
        mock_register_get.return_value = {"time": 123, "user_id": "u1"}
        mock_valid_time.return_value = True
        mock_users_get.return_value = {
            "user_id": "u1",
            "grad_semester": "2026S",
            "resume_filename": "resume.pdf",
        }
        mock_pretty_semester.return_value = "Spring 2026"
        mock_resumes_get.return_value = {
            "filename": "resume.pdf",
            "format": "pdf",
            "upload_date": "2026-01-01T00:00:00Z",
            "is_valid": 1,
        }

        resp = client.get("/self/ticket")
        assert resp.status_code == 200
        body = resp.json()
        assert body["resume"]["upload_date"] == "2026-01-01T00:00:00Z"
        assert body["resume"]["is_valid"] is True