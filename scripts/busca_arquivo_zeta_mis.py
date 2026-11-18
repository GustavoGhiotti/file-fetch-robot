"""Entrada do job ZETA MIS."""

from src.runners.logged_execution import executar_com_log
from src.runners.special_jobs import executar_zeta_mis


if __name__ == "__main__":
    executar_com_log(
        "zeta_mis",
        "busca_arquivo_zeta_mis",
        executar_zeta_mis,
    )
