"""Configuracao dos jobs do Rho."""

import re
from datetime import datetime

from src.domain.models.job_config import JobConfig
from src.infrastructure.config.env import obter_variavel


def criar_job_rho() -> JobConfig:
    """Cria a configuracao do job do Rho.

    Retorna:
        Configuracao usada para buscar arquivos do Rho.
    """
    data_hoje = datetime.now().strftime("%d%m%Y")

    return JobConfig(
        nome="rho",
        id_cedente=43,
        origem=obter_variavel("DIRETORIO_SFTP_RHO"),
        destino=obter_variavel("DIRETORIO_71_RHO"),
        extensao=".csv",
        padroes_nome=[
            re.compile(rf"^Pagamento_Acme_{data_hoje}\.csv$", re.IGNORECASE)
        ],
        servidor_destino="71",
        tipo_origem="sftp",
        converter_csv=True,
    )
