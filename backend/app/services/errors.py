"""Exceções dos serviços do Integrante 2.

Sugestão de mapeamento nas rotas (Integrante 1):

    TickerNotFoundError      -> 404  {"detail": str(exc)}
    InvalidRangeError        -> 422  {"detail": str(exc)}
    ProviderUnavailableError -> 503  {"detail": str(exc)}
"""


class MarketDataError(Exception):
    """Erro base do serviço de cotações."""


class TickerNotFoundError(MarketDataError):
    def __init__(self, ticker: str):
        self.ticker = ticker
        super().__init__(f'Ativo "{ticker}" não encontrado.')


class InvalidRangeError(MarketDataError, ValueError):
    def __init__(self, period: str, valid: tuple[str, ...]):
        self.period = period
        super().__init__(
            f'Período "{period}" inválido. Use um destes: {", ".join(valid)}.'
        )


class ProviderUnavailableError(MarketDataError):
    """Nenhum provedor respondeu (rede fora, rate limit, token inválido...)."""

    def __init__(
        self,
        message: str = "Serviço de cotações indisponível no momento. Tente novamente em instantes.",
    ):
        super().__init__(message)


class EmailSendError(Exception):
    """Falha ao enviar e-mail (SMTP fora do ar, credenciais erradas...)."""
