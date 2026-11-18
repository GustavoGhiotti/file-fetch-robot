"""Entrada do job TETA ARC."""

from src.jobs.teta_variantes import criar_job_teta_arc
from src.runners.logged_execution import executar_com_log
from src.runners.run_job import executar_job


if __name__ == "__main__":
    executar_com_log("teta_arc", "busca_arquivo_teta_arc", lambda: executar_job(criar_job_teta_arc()))
