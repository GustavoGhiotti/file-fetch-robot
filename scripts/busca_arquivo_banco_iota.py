"""Entrada do job Banco Iota."""

from src.runners.logged_execution import executar_com_log
from src.runners.special_jobs import executar_banco_iota


if __name__ == "__main__":
    executar_com_log(
        "banco_iota",
        "busca_arquivo_banco_iota",
        executar_banco_iota,
    )
