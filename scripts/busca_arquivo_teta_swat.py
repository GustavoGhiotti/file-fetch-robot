"""Entrada do job TETA Swat."""

from src.jobs.teta_variantes import criar_job_teta_swat
from src.runners.logged_execution import executar_com_log
from src.runners.run_job import executar_job


if __name__ == "__main__":
    executar_com_log(
        "teta_swat",
        "busca_arquivo_teta_swat",
        lambda: executar_job(criar_job_teta_swat()),
    )
