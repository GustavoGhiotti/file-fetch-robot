"""Configuracao dos jobs derivados do TETA."""

import re
from datetime import datetime

from src.domain.models.job_config import JobConfig
from src.infrastructure.config.env import obter_variavel


def criar_job_teta_arc() -> JobConfig:
    """Cria a configuracao do job TETA ARC."""
    data_hoje = datetime.now().strftime("%Y%m%d")

    return JobConfig(
        nome="teta_arc",
        id_cedente=90,
        origem=obter_variavel("DIRETORIO_SFTP_ORIGEM_TETAARC"),
        destino=obter_variavel("DIRETORIO_71_DESTINO_TETAARC"),
        extensao=".zip",
        padroes_nome=[
            re.compile(rf"^{data_hoje}_TELEFONE_.*\.zip$", re.IGNORECASE),
            re.compile(rf"^{data_hoje}_TELEFONES_BLOQUEADOS_.*\.zip$", re.IGNORECASE),
            re.compile(rf"^{data_hoje}_RETIRADA_.*\.zip$", re.IGNORECASE),
            re.compile(rf"^{data_hoje}_REMESSA_ARC4U_.*\.zip$", re.IGNORECASE),
        ],
        servidor_destino="71",
        tipo_origem="sftp",
        usa_chave_privada=True,
        extrair_zip=True,
        converter_csv=True,
    )


def criar_job_teta_invest() -> JobConfig:
    """Cria a configuracao do job TETA Invest."""
    data_hoje = datetime.now().strftime("%Y%m%d")

    return JobConfig(
        nome="teta_invest",
        id_cedente=77,
        origem=obter_variavel("DIRETORIO_SFTP_ORIGEM_TETAINVEST"),
        destino=obter_variavel("DIRETORIO_71_DESTINO_TETAINVEST"),
        extensao=".zip",
        padroes_nome=[
            re.compile(rf"^{data_hoje}_TELEFONE_.*\.zip$", re.IGNORECASE),
            re.compile(rf"^{data_hoje}_TELEFONES_BLOQUEADOS_.*\.zip$", re.IGNORECASE),
            re.compile(rf"^{data_hoje}_RETIRADA_.*\.zip$", re.IGNORECASE),
            re.compile(rf"^{data_hoje}_REMESSA_ARC4U_.*\.zip$", re.IGNORECASE),
        ],
        servidor_destino="71",
        tipo_origem="sftp",
        usa_chave_privada=True,
        extrair_zip=True,
        converter_csv=True,
    )


def criar_job_teta_special() -> JobConfig:
    """Cria a configuracao do job TETA Special."""
    data_hoje = datetime.now().strftime("%Y%m%d")

    return JobConfig(
        nome="teta_special",
        id_cedente=77,
        origem=obter_variavel("DIRETORIO_SFTP_ORIGEM_TETASPECIAL"),
        destino=obter_variavel("DIRETORIO_71_DESTINO_TETASPECIAL"),
        extensao=".zip",
        padroes_nome=[
            re.compile(rf"^{data_hoje}_RETIRADA_0755_OUT.*\.zip$", re.IGNORECASE),
            re.compile(rf"^{data_hoje}_REMESSA_ARC4U_0755_OUT.*\.zip$", re.IGNORECASE),
            re.compile(rf"^{data_hoje}_TELEFONE_0755_OUT.*\.zip$", re.IGNORECASE),
            re.compile(rf"^{data_hoje}_TELEFONE_BLOQUEADO_0755_OUT.*\.zip$", re.IGNORECASE),
            re.compile(rf"^{data_hoje}_TELEFONES_BLOQUEADOS_0755_OUT.*\.zip$", re.IGNORECASE),
        ],
        servidor_destino="71",
        tipo_origem="sftp",
        usa_chave_privada=True,
        extrair_zip=True,
        converter_csv=True,
    )


def criar_job_teta_swat() -> JobConfig:
    """Cria a configuracao do job TETA Swat."""
    data_hoje = datetime.now().strftime("%Y%m%d")

    return JobConfig(
        nome="teta_swat",
        id_cedente=77,
        origem=obter_variavel("DIRETORIO_SFTP_ORIGEM_SWAT"),
        destino=obter_variavel("DIRETORIO_71_DESTINO_SWAT"),
        extensao=".zip",
        padroes_nome=[
            re.compile(rf"^{data_hoje}_TELEFONES_BLOQUEADOS_.*\.zip$", re.IGNORECASE),
            re.compile(rf"^{data_hoje}_RETIRADA_.*\.zip$", re.IGNORECASE),
            re.compile(rf"^{data_hoje}_REMESSA_ARC4U_.*\.zip$", re.IGNORECASE),
        ],
        servidor_destino="71",
        tipo_origem="sftp",
        usa_chave_privada=True,
        extrair_zip=True,
        converter_csv=True,
    )


def criar_job_teta_swat_dados() -> JobConfig:
    """Cria a configuracao do job TETA Swat Dados."""
    data_hoje = datetime.now().strftime("%Y%m%d")

    return JobConfig(
        nome="teta_swat_dados",
        id_cedente=77,
        origem=obter_variavel("DIRETORIO_SFTP_ORIGEM_SWAT"),
        destino=obter_variavel("DIRETORIO_71_DADOS_SWAT"),
        extensao=".zip",
        padroes_nome=[
            re.compile(rf"^{data_hoje}_REMESSA_DADOS_SENS.VEIS_.*\.zip$", re.IGNORECASE)
        ],
        servidor_destino="71",
        tipo_origem="sftp",
        usa_chave_privada=True,
        extrair_zip=True,
        converter_csv=True,
    )
