"""Configuracao dos jobs derivados da BancoAlfa."""

import re
from datetime import datetime

from src.domain.models.job_config import JobConfig
from src.infrastructure.config.env import obter_variavel


def criar_job_bancoalfa_comp() -> JobConfig:
    """Cria a configuracao do job complementar da BancoAlfa."""
    data_hoje = datetime.now().strftime("%Y%m%d")
    destino = obter_variavel("DIRETORIO_71_BANCOALFA_comp")

    return JobConfig(
        nome="bancoalfa_comp",
        id_cedente=51,
        origem=obter_variavel("DIRETORIO_SFTP_BANCOALFA"),
        destino=destino,
        extensao=".csv",
        padroes_nome=[
            re.compile(rf"^base_complementar_clientes_EP_acme_{data_hoje}\.csv$", re.IGNORECASE),
            re.compile(rf"^base_complementar_clientes_acme_{data_hoje}\.csv$", re.IGNORECASE),
            re.compile(rf"^base_complementar_clientes_email_ep_acme_{data_hoje}\.csv$", re.IGNORECASE),
            re.compile(rf"^base_complementar_clientes_email_acme_{data_hoje}\.csv$", re.IGNORECASE),
        ],
        servidor_destino="71",
        tipo_origem="sftp",
        converter_csv=True,
        mover_restantes_para_ok=True,
        destino_ok=destino.rstrip("\\") + r"\ok",
    )


def criar_job_alfacarga() -> JobConfig:
    """Cria a configuracao do job AlfaCarga."""
    return JobConfig(
        nome="alfacarga",
        id_cedente=71,
        origem=obter_variavel("DIRETORIO_64_ORIGEM_WILLBANCK"),
        destino=obter_variavel("DIRETORIO_71_DESTINO_BANCOALFA"),
        extensao=".csv",
        padroes_nome=[],
        servidor_destino="71",
        tipo_origem="smb",
        destino_ok=obter_variavel("DIRETORIO_71_DESTINO_BANCOALFA2"),
        processamento_especial="origem tambem eh SMB",
    )
