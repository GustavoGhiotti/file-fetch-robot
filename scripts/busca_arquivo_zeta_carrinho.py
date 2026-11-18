"""Entrada do job Zeta Carrinho."""

from src.jobs.zeta import criar_job_zeta_carrinho
from src.runners.logged_execution import executar_com_log
from src.runners.run_job import executar_job


if __name__ == "__main__":
    executar_com_log(
        "zeta_carrinho",
        "busca_arquivo_zeta_carrinho",
        lambda: executar_job(criar_job_zeta_carrinho()),
    )
