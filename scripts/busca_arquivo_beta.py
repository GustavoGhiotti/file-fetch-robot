"""Entrada do job Banco Beta."""

from src.jobs.beta import criar_job_beta
from src.runners.logged_execution import executar_com_log
from src.runners.run_job import executar_job


if __name__ == "__main__":
    executar_com_log("beta", "busca_arquivo_beta", lambda: executar_job(criar_job_beta()))
