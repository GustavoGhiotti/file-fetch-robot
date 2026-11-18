"""Entrada do job complementar da BancoAlfa."""

from src.jobs.bancoalfa_variantes import criar_job_bancoalfa_comp
from src.runners.logged_execution import executar_com_log
from src.runners.run_job import executar_job


if __name__ == "__main__":
    executar_com_log(
        "bancoalfa_comp",
        "busca_arquivo_bancoalfa_comp",
        lambda: executar_job(criar_job_bancoalfa_comp()),
    )
