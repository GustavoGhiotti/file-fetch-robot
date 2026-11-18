"""Entrada do job Mu Retirada."""

from src.runners.logged_execution import executar_com_log
from src.runners.special_jobs import executar_mu_retirada


if __name__ == "__main__":
    executar_com_log(
        "mu_retirada",
        "busca_arquivo_mu_retirada",
        executar_mu_retirada,
    )
