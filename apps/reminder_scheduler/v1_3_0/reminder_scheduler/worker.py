from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from threading import Event
from typing import Callable, Optional

from appointment_agent_shared.db import SessionLocal

from .service import ReminderDispatchResult, ReminderPlanningResult, ReminderSchedulerService

logger = logging.getLogger(__name__)


@dataclass
class ReminderWorkerConfig:
    planning_interval_seconds: int = 300
    dispatch_interval_seconds: int = 45


class ReminderSchedulerWorker:
    """Lightweight polling worker for reminder planning and dispatch.

    The worker keeps the logic intentionally small so it can run locally in the
    same style as the rest of the prototype stack without a second orchestration
    framework.
    """

    def __init__(
        self,
        session_factory: Callable[[], object] = SessionLocal,
        config: Optional[ReminderWorkerConfig] = None,
    ) -> None:
        self.session_factory = session_factory
        self.config = config or ReminderWorkerConfig()

    def run_planning_once(self, policy_key: str = "global") -> ReminderPlanningResult:
        with self.session_factory() as session:
            service = ReminderSchedulerService(session)
            return service.plan_jobs(policy_key=policy_key)

    def run_dispatch_once(self, policy_key: str = "global") -> ReminderDispatchResult:
        with self.session_factory() as session:
            service = ReminderSchedulerService(session)
            return service.dispatch_due_jobs(policy_key=policy_key)

    def run_cycle_once(self, policy_key: str = "global") -> dict[str, object]:
        planning = self.run_planning_once(policy_key=policy_key)
        dispatch = self.run_dispatch_once(policy_key=policy_key)
        return {
            "planning": planning.model_dump(mode="json"),
            "dispatch": dispatch.model_dump(mode="json"),
        }

    def run_forever(self, stop_event: Optional[Event] = None, policy_key: str = "global") -> None:
        stop_event = stop_event or Event()
        logger.info("Reminder worker started for policy_key=%s", policy_key)
        while not stop_event.is_set():
            self.run_cycle_once(policy_key=policy_key)
            # The two waits intentionally share one stop token so the worker can
            # be stopped cleanly even when planning and dispatch are separated.
            if stop_event.wait(self.config.planning_interval_seconds):
                break
            if stop_event.wait(self.config.dispatch_interval_seconds):
                break
        logger.info("Reminder worker stopped for policy_key=%s", policy_key)


def build_default_worker() -> ReminderSchedulerWorker:
    return ReminderSchedulerWorker()
