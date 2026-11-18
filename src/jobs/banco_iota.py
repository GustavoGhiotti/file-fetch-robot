"""Configuracao dos jobs do Banco Iota."""

import re

from src.domain.models.job_config import JobConfig
from src.infrastructure.config.env import obter_variavel


def criar_job_banco_iota() -> JobConfig:
    """Cria a configuracao do job Banco Iota."""
    return JobConfig(
        nome="banco_iota",
        id_cedente=94,
        origem=obter_variavel("DIRETORIO_SFTP_BANCOIOTA"),
        destino=obter_variavel("DIRETORIO_71_BANCOIOTA"),
        extensao=".xlsx",
        padroes_nome=[
            re.compile(r"^BOLETOS GERADOS ACME.*\.xlsx$", re.IGNORECASE)
        ],
        servidor_destino="71",
        tipo_origem="sftp",
        processamento_especial="possui tratamento proprio de xlsx",
    )
