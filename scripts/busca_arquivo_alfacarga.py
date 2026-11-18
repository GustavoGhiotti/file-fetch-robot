"""Entrada do job AlfaCarga."""

from src.runners.logged_execution import executar_com_log
from src.runners.special_jobs import executar_alfacarga


if __name__ == "__main__":
    executar_com_log("alfacarga", "busca_arquivo_alfacarga", executar_alfacarga)
