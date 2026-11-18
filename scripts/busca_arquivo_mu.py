"""Entrada do job Mu Pagamentos Pix."""

from src.runners.logged_execution import executar_com_log
from src.runners.special_jobs import executar_mu_pagamentos


if __name__ == "__main__":
    executar_com_log(
        "mu",
        "busca_arquivo_mu",
        executar_mu_pagamentos,
    )
