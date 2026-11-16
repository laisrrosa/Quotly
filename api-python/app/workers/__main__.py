"""Worker de alertas como processo separado.

    python -m app.workers          # roda para sempre, a cada N minutos
    python -m app.workers --once   # roda um único ciclo e sai (bom para cron)
"""
from __future__ import annotations

import argparse
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from app.core.logging_config import log_event, setup_logging
from app.workers.scheduler import build_monitor, configure

logger = logging.getLogger("app.workers")


def main() -> None:
    parser = argparse.ArgumentParser(description="Worker de alertas de preço do Quotly")
    parser.add_argument("--once", action="store_true", help="executa um ciclo e encerra")
    args = parser.parse_args()

    setup_logging()
    try:
        monitor = build_monitor()
    except RuntimeError as exc:  # modelos/sessão do back-end não encontrados
        raise SystemExit(f"Erro: {exc}")

    if args.once:
        monitor.run_cycle()
        return

    scheduler = configure(BlockingScheduler(), monitor)
    log_event(logger, logging.INFO, "alert_worker_started")
    try:
        scheduler.start()  # bloqueia até Ctrl+C
    except (KeyboardInterrupt, SystemExit):
        log_event(logger, logging.INFO, "alert_worker_stopped")


if __name__ == "__main__":
    main()
