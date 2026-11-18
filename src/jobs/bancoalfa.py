"""Configuracao dos jobs da BancoAlfa."""

import re
from datetime import datetime

from src.domain.models.job_config import JobConfig
from src.infrastructure.config.env import obter_variavel


def criar_job_bancoalfa() -> JobConfig:
    """Cria a configuracao do job principal da BancoAlfa.

    Retorna:
        Configuracao usada para buscar o arquivo da BancoAlfa.
    """
    data_hoje = datetime.now().strftime("%Y%m%d")

    return JobConfig(
        nome="bancoalfa",
        id_cedente=51,
        origem=obter_variavel("DIRETORIO_SFTP_BANCOALFA"),
        destino=obter_variavel("DIRETORIO_71_BANCOALFA"),
        extensao=".csv",
        padroes_nome=[
            re.compile(rf"^base_blocklist_telefones_{data_hoje}\.csv$", re.IGNORECASE)
        ],
        servidor_destino="71",
        tipo_origem="sftp",
        converter_csv=True,
    )
