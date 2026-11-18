"""Entrada do job TETA Invest."""

from src.jobs.teta_variantes import criar_job_teta_invest
from src.runners.logged_execution import executar_com_log
from src.runners.run_job import executar_job


if __name__ == "__main__":
    executar_com_log(
        "teta_invest",
        "busca_arquivo_teta_invest",
        lambda: executar_job(criar_job_teta_invest()),
    )
