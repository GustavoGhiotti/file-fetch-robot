"""Configuracao dos jobs da Zeta."""

import re
from datetime import datetime

from src.domain.models.job_config import JobConfig
from src.infrastructure.config.env import obter_variavel


def criar_job_zeta_carrinho() -> JobConfig:
    """Cria a configuracao do job Zeta Carrinho."""
    data_hoje = datetime.now().strftime("%Y%m%d")

    return JobConfig(
        nome="zeta_carrinho",
        id_cedente=71,
        origem=obter_variavel("DIRETORIO_SFTP_ZETA_CARRINHO"),
        destino=obter_variavel("DIRETORIO_71_ZETA_CARRINHO"),
        extensao=".zip",
        padroes_nome=[
            re.compile(rf"^TXT__SISTEMA_ConsultaLivre_APICONS_{data_hoje}.*\.zip$", re.IGNORECASE)
        ],
        servidor_destino="71",
        tipo_origem="sftp",
        extrair_zip=True,
        verificar_existencia_exata=True,
        verificar_por_prefixo=False,
    )


def criar_job_zeta_ocorrencia() -> JobConfig:
    """Cria a configuracao do job Zeta Ocorrencia."""
    data_hoje = datetime.now().strftime("%Y%m%d")

    return JobConfig(
        nome="zeta_ocorrencia",
        id_cedente=71,
        origem=obter_variavel("DIRETORIO_SFTP_ZETA_OCORRENCIA"),
        destino=obter_variavel("DIRETORIO_71_ZETA_OCORRENCIA"),
        extensao=".zip",
        padroes_nome=[
            re.compile(rf"^TXT__SISTEMA_ConsultaLivre_REL_OCOA_{data_hoje}.*\.zip$", re.IGNORECASE)
        ],
        servidor_destino="71",
        tipo_origem="sftp",
        extrair_zip=True,
        verificar_existencia_exata=True,
        verificar_por_prefixo=False,
    )


def criar_job_zeta_remessa() -> JobConfig:
    """Cria a configuracao do job Zeta Remessa."""
    return JobConfig(
        nome="zeta_remessa",
        id_cedente=71,
        origem=obter_variavel("DIRETORIO_SFTP_ZETA_REMESSA"),
        destino=obter_variavel("DIRETORIO_71_ZETA_REMESSA"),
        extensao=".zip",
        padroes_nome=[],
        servidor_destino="71",
        tipo_origem="sftp",
        extrair_zip=True,
        selecionar_mais_recente_do_dia=True,
        verificar_existencia_exata=True,
        verificar_por_prefixo=False,
    )
