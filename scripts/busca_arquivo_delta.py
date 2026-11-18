"""Entrada do job Delta no servidor 72."""

from src.runners.logged_execution import executar_com_log
from src.runners.special_jobs import executar_delta


if __name__ == "__main__":
    executar_com_log("delta", "busca_arquivo_delta", lambda: executar_delta("72"))
