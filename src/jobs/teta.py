"""Configuracao dos jobs do TETA."""

import re
from datetime import datetime

from src.domain.models.job_config import JobConfig
from src.infrastructure.config.env import obter_variavel


def criar_job_teta() -> JobConfig:
    """Cria a configuracao do job principal do TETA.

    Retorna:
        Configuracao usada para buscar arquivos ZIP do TETA.
    """
    data_hoje = datetime.now().strftime("%Y%m%d")

    return JobConfig(
        nome="teta",
        id_cedente=77,
        origem=obter_variavel("DIRETORIO_SFTP_ORIGEM_CONSUMER"),
        destino=obter_variavel("DIRETORIO_71_TETA"),
        extensao=".zip",
        padroes_nome=[
            re.compile(rf"^{data_hoje}_TELEFONES_BLOQUEADOS_.*\.zip$", re.IGNORECASE),
            re.compile(rf"^{data_hoje}_RETIRADA_.*\.zip$", re.IGNORECASE),
            re.compile(rf"^{data_hoje}_REMESSA_.*\.zip$", re.IGNORECASE),
        ],
        servidor_destino="71",
        tipo_origem="sftp",
        usa_chave_privada=True,
        extrair_zip=True,
        converter_csv=True,
    )
