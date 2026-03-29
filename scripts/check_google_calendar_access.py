from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_TOKEN_PATH = Path("local-secrets/google/token.json")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sanity-check that the configured Google Calendar is reachable with the local token."
    )
    parser.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_PATH)
    parser.add_argument("--calendar-id", required=True)
    return parser


def load_token(token_path: Path) -> dict:
    return json.loads(token_path.read_text(encoding="utf-8"))


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()
    if not args.token_file.exists():
        parser.error("Token file not found. Run scripts/get_google_refresh_token.py first.")

    token_data = load_token(args.token_file)

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover - depends on optional local packages
        raise RuntimeError(
            "Missing Google API packages. Install them with: pip install -e '.[google]'"
        ) from exc

    credentials = Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("GOOGLE_TOKEN_URI") or token_data.get("token_uri"),
        client_id=token_data.get("GOOGLE_CLIENT_ID"),
        client_secret=token_data.get("GOOGLE_CLIENT_SECRET"),
        scopes=token_data.get("scopes") or ["https://www.googleapis.com/auth/calendar"],
    )
    service = build("calendar", "v3", credentials=credentials)
    calendar = service.calendars().get(calendarId=args.calendar_id).execute()
    print("Calendar access check succeeded.")
    print(f"calendar_id={calendar.get('id')}")
    print(f"summary={calendar.get('summary')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
