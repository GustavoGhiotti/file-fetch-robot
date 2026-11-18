"""Configuracao dos jobs do Banco Beta."""

import re
from datetime import datetime

from src.domain.models.job_config import JobConfig
from src.infrastructure.config.env import obter_variavel


def criar_job_beta() -> JobConfig:
    """Cria a configuracao do job do Banco Beta.

    Retorna:
        Configuracao usada para buscar arquivos do Banco Beta.
    """
    data_hoje = datetime.now().strftime("%Y%m%d")

    return JobConfig(
        nome="beta",
        id_cedente=81,
        origem=obter_variavel("DIRETORIO_SFTP_ORIGEM_BETA"),
        destino=obter_variavel("DIRETORIO_71_DESTINO_BETA"),
        extensao=".zip",
        padroes_nome=[
            re.compile(rf"^{data_hoje}_PARCELAS_BETA_.*\.zip$", re.IGNORECASE),
            re.compile(rf"^{data_hoje}_REMESSA_BETA_.*\.zip$", re.IGNORECASE),
        ],
        servidor_destino="71",
        tipo_origem="sftp",
        usa_chave_privada=True,
        extrair_zip=True,
        converter_csv=True,
    )
