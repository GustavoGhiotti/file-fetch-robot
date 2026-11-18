"""Configuracao dos jobs do Delta."""

from src.domain.models.job_config import JobConfig
from src.infrastructure.config.env import obter_variavel


def criar_job_delta() -> JobConfig:
    """Cria a configuracao do job Delta para o servidor 72."""
    return JobConfig(
        nome="delta",
        id_cedente=65,
        origem=obter_variavel("DIRETORIO_SFTP_DELTA"),
        destino=obter_variavel("DIRETORIO_72_DESTINO_DELTA"),
        extensao=".zip",
        padroes_nome=[],
        servidor_destino="72",
        tipo_origem="sftp",
        processamento_especial="deduplica por assinatura (nome|tamanho|mtime) no banco",
    )


def criar_job_delta_71() -> JobConfig:
    """Cria a configuracao do job Delta para o servidor 71."""
    return JobConfig(
        nome="delta_71",
        id_cedente=65,
        origem=obter_variavel("DIRETORIO_SFTP_DELTA"),
        destino=obter_variavel("DIRETORIO_71_DESTINO_DELTA"),
        extensao=".zip",
        padroes_nome=[],
        servidor_destino="71",
        tipo_origem="sftp",
        processamento_especial="deduplica por assinatura (nome|tamanho|mtime) no banco",
    )
