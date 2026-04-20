from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from appointment_agent_shared.db import Base, get_session
from appointment_agent_shared.repositories import AddressAppointmentLinkRepository, AddressRepository
from reminder_scheduler.v1_3_6.reminder_scheduler.app import app
from reminder_scheduler.v1_3_6.reminder_scheduler.service import (
    ReminderAppointmentInput,
    ReminderMode,
    ReminderPolicyInput,
)


DB_PATH = Path(gettempdir()) / f"appointment_agent_reminder_v136_{uuid4().hex}.db"
ENGINE = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=ENGINE)


def _client() -> TestClient:
    def _override_session():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = _override_session
    return TestClient(app)


def test_v136_core_routes_use_the_new_release_prefix() -> None:
    client = _client()

    help_response = client.get("/api/reminders/v1.3.6/help")
    root_response = client.get("/api/reminders/v1.3.6/")
    health_response = client.get("/api/reminders/v1.3.6/health")

    assert help_response.status_code == 200
    assert help_response.json()["version"] == "v1.3.6"

    assert root_response.status_code == 200
    assert root_response.json()["help_path"] == "/api/reminders/v1.3.6/help"
    assert root_response.json()["health_path"] == "/api/reminders/v1.3.6/health"

    assert health_response.status_code == 200
    assert health_response.json()["version"] == "v1.3.6"


def test_v136_rebuild_still_plans_jobs_on_the_release_line() -> None:
    client = _client()

    start_time = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
    policy = ReminderPolicyInput(
        tenant_id="default",
        policy_key="v136-demo",
        enabled=True,
        mode=ReminderMode.MANUAL,
        reminder_count=2,
        first_reminder_hours_before=24,
        second_reminder_hours_before=2,
        channel_email_enabled=True,
        channel_voice_enabled=False,
        channel_rcs_sms_enabled=True,
    )
    appointment = ReminderAppointmentInput(
        appointment_external_id="appt-v136-demo",
        title="Reminder v1.3.6 Demo",
        start_time=start_time,
        end_time=start_time + timedelta(minutes=30),
        timezone="UTC",
        tenant_id="default",
        customer_id="customer-v136",
        email="customer@example.test",
        phone="+491701234567",
        status="scheduled",
        metadata={"policy_key": "v136-demo"},
    )

    rebuild_response = client.post(
        "/api/reminders/v1.3.6/rebuild",
        json={
            "policy": policy.model_dump(mode="json"),
            "appointments": [appointment.model_dump(mode="json")],
            "replace_existing": True,
        },
    )
    jobs_response = client.get("/api/reminders/v1.3.6/jobs")

    assert rebuild_response.status_code == 200
    assert rebuild_response.json()["planned_jobs"] == 2
    assert jobs_response.status_code == 200
    assert jobs_response.json()["version"] == "v1.3.6"
    assert jobs_response.json()["count"] == 2


def test_v136_rebuild_uses_address_linkage_from_shared_address_database() -> None:
    session = TestingSessionLocal()
    try:
        AddressRepository(session).create_or_update(
            address_id="addr-v136-001",
            display_name="Anna Berger",
            tenant_id="default",
            city="Berlin",
            phone="+491701234567",
            correlation_ref="corr-v136-001",
        )
        AddressAppointmentLinkRepository(session).link(
            link_id="addr-link-v136-001",
            address_id="addr-v136-001",
            appointment_external_id="appt-v136-linked",
            booking_reference="book-v136-linked",
            calendar_ref="gcal-v136-linked",
            correlation_ref="corr-v136-001",
            tenant_id="default",
        )
    finally:
        session.close()

    client = _client()
    start_time = datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc)
    policy = ReminderPolicyInput(
        tenant_id="default",
        policy_key="v136-linked",
        enabled=True,
        mode=ReminderMode.MANUAL,
        reminder_count=1,
        first_reminder_hours_before=24,
        channel_email_enabled=True,
        channel_voice_enabled=False,
        channel_rcs_sms_enabled=True,
    )
    appointment = ReminderAppointmentInput(
        appointment_external_id="appt-v136-linked",
        title="Reminder linkage demo",
        start_time=start_time,
        end_time=start_time + timedelta(minutes=30),
        timezone="UTC",
        tenant_id="default",
        customer_id="customer-v136-linked",
        email="linked@example.test",
        phone="+491701234567",
        status="scheduled",
        metadata={"policy_key": "v136-linked", "booking_reference": "book-v136-linked"},
    )

    rebuild_response = client.post(
        "/api/reminders/v1.3.6/rebuild",
        json={
            "policy": policy.model_dump(mode="json"),
            "appointments": [appointment.model_dump(mode="json")],
            "replace_existing": True,
        },
    )
    assert rebuild_response.status_code == 200

    jobs_response = client.get("/api/reminders/v1.3.6/jobs")
    assert jobs_response.status_code == 200
    linked_job = next(
        job
        for job in jobs_response.json()["jobs"]
        if job["appointment_external_id"] == "appt-v136-linked"
    )
    assert linked_job["address_id"] == "addr-v136-001"
    assert linked_job["correlation_ref"] == "corr-v136-001"
    assert linked_job["payload"]["address_id"] == "addr-v136-001"
