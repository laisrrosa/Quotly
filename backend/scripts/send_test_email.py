"""Envia um e-mail de alerta de exemplo (teste manual do SMTP).

    python -m scripts.send_test_email voce@email.com
    python -m scripts.send_test_email voce@email.com --condition below

Com EMAIL_BACKEND=console o e-mail só aparece no log; use EMAIL_BACKEND=smtp
(Mailtrap, Gmail...) para enviar de verdade.
"""
import argparse

from app.core.logging_config import setup_logging
from app.services.email_service import send_alert_email
from app.services.errors import EmailSendError


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("to_email")
    parser.add_argument("--condition", choices=["above", "below"], default="above")
    args = parser.parse_args()

    setup_logging()
    try:
        send_alert_email(
            to_email=args.to_email,
            user_name="Maria",
            ticker="PETR4",
            condition=args.condition,
            target_price=38.00,
            current_price=38.50 if args.condition == "above" else 37.40,
        )
    except EmailSendError as exc:
        raise SystemExit(f"Erro: {exc}")
    print("OK")


if __name__ == "__main__":
    main()
