from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_CREDENTIALS_PATH = Path("local-secrets/google/credentials.json")
DEFAULT_TOKEN_PATH = Path("local-secrets/google/token.json")
GOOGLE_CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar"


def load_oauth_client(credentials_path: Path) -> dict[str, Any]:
    data = json.loads(credentials_path.read_text(encoding="utf-8"))
    installed = data.get("installed")
    if not isinstance(installed, dict):
        raise ValueError("The OAuth client JSON must contain an 'installed' section for a desktop app.")
    return installed


def extract_env_values(oauth_client: dict[str, Any]) -> dict[str, str]:
    redirect_uris = oauth_client.get("redirect_uris") or ["http://localhost"]
    return {
        "GOOGLE_CLIENT_ID": oauth_client.get("client_id", ""),
        "GOOGLE_CLIENT_SECRET": oauth_client.get("client_secret", ""),
        "GOOGLE_REDIRECT_URI": redirect_uris[0],
        "GOOGLE_TOKEN_URI": oauth_client.get("token_uri", "https://oauth2.googleapis.com/token"),
    }


def run_browser_oauth_flow(credentials_path: Path, scope: str) -> dict[str, Any]:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:  # pragma: no cover - depends on optional local packages
        raise RuntimeError(
            "Missing Google OAuth packages. Install them with: pip install -e '.[google]'"
        ) from exc

    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), scopes=[scope])
    credentials = flow.run_local_server(port=0)
    return {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "scopes": list(credentials.scopes or []),
    }


def save_token_file(token_path: Path, token_payload: dict[str, Any]) -> None:
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(json.dumps(token_payload, indent=2), encoding="utf-8")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Retrieve a local Google Calendar refresh token for Appointment Agent v1.1.0 preparation."
    )
    parser.add_argument(
        "--credentials",
        type=Path,
        default=DEFAULT_CREDENTIALS_PATH,
        help="Path to the local desktop OAuth client JSON.",
    )
    parser.add_argument(
        "--token-output",
        type=Path,
        default=DEFAULT_TOKEN_PATH,
        help="Ignored local output file for the retrieved token payload.",
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Do not save a token file. Print the token data only.",
    )
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    credentials_path: Path = args.credentials
    if not credentials_path.exists():
        parser.error(
            "OAuth client file not found. Place it at local-secrets/google/credentials.json "
            "or pass --credentials /path/to/file.json"
        )

    oauth_client = load_oauth_client(credentials_path)
    env_values = extract_env_values(oauth_client)
    token_payload = run_browser_oauth_flow(credentials_path, GOOGLE_CALENDAR_SCOPE)

    print("Google OAuth flow completed.")
    print("Never commit the OAuth client file, token file, or your local .env.")
    print()
    print("Copy these values into your local .env:")
    print(f"GOOGLE_CLIENT_ID={env_values['GOOGLE_CLIENT_ID']}")
    print(f"GOOGLE_CLIENT_SECRET={env_values['GOOGLE_CLIENT_SECRET']}")
    print(f"GOOGLE_REDIRECT_URI={env_values['GOOGLE_REDIRECT_URI']}")
    print(f"GOOGLE_REFRESH_TOKEN={token_payload.get('refresh_token') or ''}")
    print()

    if args.print_only:
        print("Print-only mode enabled. No token file was written.")
    else:
        save_token_file(args.token_output, {**env_values, **token_payload})
        print(f"Sensitive token data was saved locally to: {args.token_output}")
        print("That file is ignored by Git. Do not move it into a tracked folder.")

    if not token_payload.get("refresh_token"):
        print()
        print("Warning: Google did not return a refresh token.")
        print("Try revoking previous consent and run the helper again so you get a fresh offline token.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
