"""Consulta uma cotação real pelo terminal (teste manual dos provedores).

    python -m scripts.check_quote PETR4
    python -m scripts.check_quote AAPL --history 1mo
"""
import argparse
import json

from app.core.logging_config import setup_logging
from app.services import market_data
from app.services.errors import MarketDataError


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker")
    parser.add_argument("--history", choices=market_data.VALID_RANGES, help="mostra também o histórico")
    args = parser.parse_args()

    setup_logging()
    try:
        print(json.dumps(market_data.get_current_quote(args.ticker), indent=2, ensure_ascii=False))
        if args.history:
            points = market_data.get_historical_quotes(args.ticker, args.history)
            print(f"\nHistórico {args.history}: {len(points)} pregões")
            for point in points:
                print(f"  {point['date']}  {point['close']:.2f}")
    except MarketDataError as exc:
        raise SystemExit(f"Erro: {exc}")


if __name__ == "__main__":
    main()
