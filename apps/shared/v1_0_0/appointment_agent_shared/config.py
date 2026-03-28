from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Appointment Agent"
    app_version: str = "v1.0.4-patch1"
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
    demo_base_path: str = "/ui/demo-monitoring/v1.0.4-patch1"

    model_config = SettingsConfigDict(
        env_prefix="APPOINTMENT_AGENT_",
        extra="ignore",
    )


settings = Settings()
