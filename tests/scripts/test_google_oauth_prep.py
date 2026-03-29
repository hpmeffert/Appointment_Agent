from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "get_google_refresh_token.py"
SPEC = spec_from_file_location("get_google_refresh_token", MODULE_PATH)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_load_oauth_client_reads_desktop_client(tmp_path: Path) -> None:
    credentials_file = tmp_path / "credentials.json"
    credentials_file.write_text(
        """
        {
          "installed": {
            "client_id": "client-id",
            "client_secret": "client-secret",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"]
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    oauth_client = MODULE.load_oauth_client(credentials_file)

    assert oauth_client["client_id"] == "client-id"
    assert oauth_client["client_secret"] == "client-secret"


def test_extract_env_values_uses_first_redirect_uri() -> None:
    values = MODULE.extract_env_values(
        {
            "client_id": "client-id",
            "client_secret": "client-secret",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost", "http://127.0.0.1"],
        }
    )

    assert values["GOOGLE_CLIENT_ID"] == "client-id"
    assert values["GOOGLE_CLIENT_SECRET"] == "client-secret"
    assert values["GOOGLE_REDIRECT_URI"] == "http://localhost"
