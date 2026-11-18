"""Entrada do job BancoAlfa."""

from src.jobs.bancoalfa import criar_job_bancoalfa
from src.runners.logged_execution import executar_com_log
from src.runners.run_job import executar_job


if __name__ == "__main__":
    executar_com_log(
        "bancoalfa",
        "busca_arquivo_bancoalfa",
        lambda: executar_job(criar_job_bancoalfa()),
    )
