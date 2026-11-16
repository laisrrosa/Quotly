"""Agendamento do monitor de alertas com APScheduler.

Duas formas de rodar:

1. Junto com a API (mesmo processo), no lifespan do FastAPI:

       from contextlib import asynccontextmanager
       from app.workers.scheduler import start_scheduler, stop_scheduler

       @asynccontextmanager
       async def lifespan(app):
           start_scheduler()
           yield
           stop_scheduler()

       app = FastAPI(lifespan=lifespan)

2. Como processo separado:  `python -m app.workers`
"""
from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler

from app.core.logging_config import log_event
from app.core.worker_config import get_settings
from app.workers.alert_monitor import AlertMonitor

logger = logging.getLogger(__name__)

JOB_ID = "quotly-alert-monitor"
_scheduler: BaseScheduler | None = None


def build_monitor() -> AlertMonitor:
    from app.workers.alert_repository import build_default_repository

    return AlertMonitor(build_default_repository())


def configure(scheduler: BaseScheduler, monitor: AlertMonitor | None = None) -> BaseScheduler:
    """Registra o job periódico em `scheduler` (sem iniciá-lo)."""
    monitor = monitor or build_monitor()
    minutes = get_settings().alert_check_interval_minutes
    scheduler.add_job(
        monitor.run_cycle,
        trigger="interval",
        minutes=minutes,
        id=JOB_ID,
        replace_existing=True,
        max_instances=1,  # nunca dois ciclos ao mesmo tempo
        coalesce=True,  # se atrasar, roda uma vez só (não acumula execuções)
        next_run_time=datetime.now(),  # primeiro ciclo já na subida
    )
    log_event(logger, logging.INFO, "alert_scheduler_configured", interval_minutes=minutes)
    return scheduler


def start_scheduler(monitor: AlertMonitor | None = None) -> BaseScheduler:
    """Inicia o worker em uma thread de background (para usar junto com a API)."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return _scheduler
    _scheduler = configure(BackgroundScheduler(daemon=True), monitor)
    _scheduler.start()
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log_event(logger, logging.INFO, "alert_scheduler_stopped")
    _scheduler = None
