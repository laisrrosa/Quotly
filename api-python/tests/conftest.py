"""Prepara o ambiente de teste para rodar junto com o back-end real.

As variáveis precisam existir antes de `app.core.config` ser importado (a
classe Settings do back-end exige SECRET_KEY) e o banco é um arquivo
temporário, para nunca tocar no `quotly.db` de verdade.
"""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="quotly-tests-")
os.environ["SECRET_KEY"] = "chave-so-para-testes"
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
