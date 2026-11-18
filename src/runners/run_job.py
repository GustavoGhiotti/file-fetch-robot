"""Runner padrao para executar um job configurado."""

import os

from src.application.use_cases.executar_busca_arquivos import ExecutarBuscaArquivo
from src.domain.models.job_config import JobConfig
from src.infrastructure.config.settings import (
    obter_config_banco_66,
    obter_config_servidor,
    resolver_destino_execucao,
)
from src.infrastructure.ftp.ftp_client import FTPClient
from src.infrastructure.repositories.credentials_repository import DatabaseCredentialsRepository
from src.infrastructure.sftp.sftp_client import SFTPClient
from src.infrastructure.smb.smb_client import SMBClient


def executar_job(config: JobConfig) -> list[str]:
    """Executa um job usando a infraestrutura configurada.

    Recebe:
        config: configuracao do job.

    Retorna:
        Lista com arquivos gerados no destino.
    """
    config_db = obter_config_banco_66(config.banco)
    credencial = DatabaseCredentialsRepository(config_db).obter_credencial(config.id_cedente)

    if config.usar_origem_banco and credencial.origem_carga:
        config.origem = credencial.origem_carga

    if config.usar_destino_banco and credencial.destino_carga:
        config.destino = credencial.destino_carga

    config.destino = resolver_destino_execucao(config.destino, config.nome)
    if config.destino_ok:
        config.destino_ok = resolver_destino_execucao(config.destino_ok, config.nome + "_ok")

    cliente_remoto = _criar_cliente_remoto(config, credencial)
    servidor_destino = _criar_servidor_destino(config.servidor_destino)

    try:
        return ExecutarBuscaArquivo(cliente_remoto, servidor_destino, config).executar()
    finally:
        fechar = getattr(cliente_remoto, "fechar", None)
        if fechar:
            fechar()


def _criar_cliente_remoto(config: JobConfig, credencial):
    """Cria FTP ou SFTP de acordo com o job."""
    if config.tipo_origem == "sftp":
        key_file = _resolver_chave_privada(credencial.senha) if config.usa_chave_privada else None
        password = None if config.usa_chave_privada else credencial.senha
        return SFTPClient(
            hostname=credencial.hostname,
            user=credencial.usuario,
            password=password,
            port=credencial.porta,
            key_file=key_file,
        )

    if config.tipo_origem == "ftp":
        return FTPClient(
            hostname=credencial.hostname,
            user=credencial.usuario,
            password=credencial.senha,
            port=credencial.porta or 21,
        )

    raise ValueError(f"Tipo de origem nao suportado no runner padrao: {config.tipo_origem}")


def _criar_servidor_destino(numero_servidor: str) -> SMBClient:
    """Cria e conecta o cliente SMB de destino."""
    config_sv = obter_config_servidor(numero_servidor)
    servidor = SMBClient(
        config_sv["ipServidor"],
        config_sv["usuario"],
        config_sv["senha"],
    )
    servidor.conectar()
    return servidor


def _resolver_chave_privada(nome_arquivo: str) -> str:
    """Monta caminho da chave privada dentro da pasta senhas."""
    return os.path.join(os.getcwd(), "senhas", nome_arquivo)
