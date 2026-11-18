"""Entrada do job Rho."""

from src.jobs.rho import criar_job_rho
from src.runners.logged_execution import executar_com_log
from src.runners.run_job import executar_job


if __name__ == "__main__":
    executar_com_log(
        "rho",
        "busca_arquivo_rho",
        lambda: executar_job(criar_job_rho()),
    )
