"""Entrada do job Mu BSC."""

from src.runners.logged_execution import executar_com_log
from src.runners.special_jobs import executar_mu_bsc


if __name__ == "__main__":
    executar_com_log(
        "mu_bsc",
        "busca_arquivo_mu_bsc",
        executar_mu_bsc,
    )
