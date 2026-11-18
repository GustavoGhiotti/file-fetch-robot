"""Entrada do job TETA Special."""

from src.jobs.teta_variantes import criar_job_teta_special
from src.runners.logged_execution import executar_com_log
from src.runners.run_job import executar_job


if __name__ == "__main__":
    executar_com_log(
        "teta_special",
        "busca_arquivo_teta_special",
        lambda: executar_job(criar_job_teta_special()),
    )
