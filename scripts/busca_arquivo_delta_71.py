"""Entrada do job Delta no servidor 71."""

from src.runners.logged_execution import executar_com_log
from src.runners.special_jobs import executar_delta


if __name__ == "__main__":
    executar_com_log(
        "delta_71",
        "busca_arquivo_delta_71",
        lambda: executar_delta("71"),
    )
