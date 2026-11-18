"""Entrada do job de retorno Upsilon."""

from src.jobs.upsilon_retorno import executar_retorno_upsilon
from src.runners.logged_execution import executar_com_log


if __name__ == "__main__":
    executar_com_log(
        "upsilon_retorno",
        "busca_arquivo_upsilon_retorno",
        executar_retorno_upsilon,
    )
