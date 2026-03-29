from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Appointment Agent"
    app_version: str = "v1.1.0-patch6"
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    log_level: str = "info"
    silence_threshold_ms: int = 1300
    db_url: str = "sqlite:///./data/appointment_agent.db"
    safe_diagnostics: bool = True
    booking_window_days: int = 30
    max_slots_per_offer: int = 3
    default_duration_minutes: int = 30
    slot_hold_minutes: int = 10
    reschedule_cutoff_hours: int = 24
    quiet_hours: str = "21:00-08:00"
    default_language: str = "en"
    ask_confirmation_before_commit: bool = True
    human_handoff_enabled: bool = True
    idempotency_enabled: bool = True
    google_mock_mode: bool = True
    lekab_mock_mode: bool = True
    demo_base_path: str = "/ui/demo-monitoring/v1.1.0-patch6"
    google_real_integration_enabled: bool = Field(default=False, validation_alias="GOOGLE_REAL_INTEGRATION_ENABLED")
    google_client_id: str = Field(default="", validation_alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", validation_alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(default="http://localhost", validation_alias="GOOGLE_REDIRECT_URI")
    google_refresh_token: str = Field(default="", validation_alias="GOOGLE_REFRESH_TOKEN")
    google_calendar_id: str = Field(default="", validation_alias="GOOGLE_CALENDAR_ID")
    google_default_timezone: str = Field(default="Europe/Berlin", validation_alias="GOOGLE_DEFAULT_TIMEZONE")
    google_contacts_enabled: bool = Field(default=False, validation_alias="GOOGLE_CONTACTS_ENABLED")
    google_test_mode_default: Literal["simulation", "test"] = Field(
        default="simulation",
        validation_alias="GOOGLE_TEST_MODE_DEFAULT",
    )

    model_config = SettingsConfigDict(
        env_prefix="APPOINTMENT_AGENT_",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_google_runtime(self) -> "Settings":
        if self.google_mock_mode and self.google_real_integration_enabled:
            raise ValueError(
                "APPOINTMENT_AGENT_GOOGLE_MOCK_MODE=true conflicts with GOOGLE_REAL_INTEGRATION_ENABLED=true."
            )
        if self.google_test_mode_default == "test" and not self.google_real_integration_enabled:
            raise ValueError(
                "GOOGLE_TEST_MODE_DEFAULT=test requires GOOGLE_REAL_INTEGRATION_ENABLED=true."
            )
        if self.google_real_integration_enabled:
            required_values = {
                "GOOGLE_CLIENT_ID": self.google_client_id,
                "GOOGLE_CLIENT_SECRET": self.google_client_secret,
                "GOOGLE_REFRESH_TOKEN": self.google_refresh_token,
                "GOOGLE_CALENDAR_ID": self.google_calendar_id,
            }
            missing = [key for key, value in required_values.items() if not value]
            if missing:
                raise ValueError(
                    "Real Google integration is enabled, but required settings are missing: {}".format(
                        ", ".join(missing)
                    )
                )
        return self


settings = Settings()
