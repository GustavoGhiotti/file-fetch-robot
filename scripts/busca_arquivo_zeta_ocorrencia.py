"""Entrada do job Zeta Ocorrencia."""

from src.jobs.zeta import criar_job_zeta_ocorrencia
from src.runners.logged_execution import executar_com_log
from src.runners.run_job import executar_job


if __name__ == "__main__":
    executar_com_log(
        "zeta_ocorrencia",
        "busca_arquivo_zeta_ocorrencia",
        lambda: executar_job(criar_job_zeta_ocorrencia()),
    )
