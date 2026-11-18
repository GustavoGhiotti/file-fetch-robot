"""Entrada do job Mu Batimento."""

from src.runners.logged_execution import executar_com_log
from src.runners.special_jobs import executar_mu_bat


if __name__ == "__main__":
    executar_com_log(
        "mu_bat",
        "busca_arquivo_mu_bat",
        executar_mu_bat,
    )
