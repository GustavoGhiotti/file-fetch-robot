"""Entrada do job TETA."""

from src.jobs.teta import criar_job_teta
from src.runners.logged_execution import executar_com_log
from src.runners.run_job import executar_job


if __name__ == "__main__":
    executar_com_log("teta", "busca_arquivo_teta", lambda: executar_job(criar_job_teta()))
