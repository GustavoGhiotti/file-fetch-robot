"""Funcoes para copiar e organizar arquivos."""

import os
import shutil
from re import Pattern

import smbclient


TAMANHO_BUFFER = 1024 * 1024 * 8


def montar_caminho_smb(pasta_destino: str, nome_arquivo: str) -> str:
    """Monta o caminho final de um arquivo no SMB."""
    return pasta_destino.rstrip("\\") + "\\" + nome_arquivo


def montar_caminho_remoto(pasta_origem: str, nome_arquivo: str) -> str:
    """Monta o caminho final de um arquivo remoto."""
    return pasta_origem.rstrip("/") + "/" + nome_arquivo


def obter_prefixo_arquivo(nome_arquivo: str) -> str:
    """Pega o nome do arquivo sem a extensao."""
    return os.path.splitext(nome_arquivo)[0]


def arquivo_ja_processado(nome_arquivo: str, arquivos_existentes: list[str]) -> bool:
    """Verifica se o arquivo ja existe no destino usando prefixo."""
    prefixo = obter_prefixo_arquivo(nome_arquivo)
    return any(
        arquivo.lower().startswith(prefixo.lower())
        for arquivo in arquivos_existentes
    )


def copiar_remoto_para_smb(cliente_remoto, origem_remota: str, destino_smb: str) -> None:
    """Copia um arquivo remoto para o SMB."""
    with cliente_remoto.abrir_arquivo(origem_remota) as origem:
        with smbclient.open_file(destino_smb, mode="wb") as destino:
            shutil.copyfileobj(origem, destino, length=TAMANHO_BUFFER)
            destino.flush()


def copiar_sftp_para_smb(cliente_sftp, origem_remota: str, destino_smb: str) -> None:
    """Mantem compatibilidade com chamadas antigas de copia SFTP para SMB."""
    copiar_remoto_para_smb(cliente_sftp, origem_remota, destino_smb)


def caminho_existe_smb(caminho: str) -> bool:
    """Verifica se um caminho existe no SMB."""
    return smbclient.path.exists(caminho)


def mover_restantes_por_padrao(
    destino_principal: str,
    pasta_destino: str,
    padroes: list[Pattern],
) -> None:
    """Move arquivos fora dos padroes para outra pasta SMB."""
    if not smbclient.path.exists(pasta_destino):
        print(f"A pasta de destino nao existe: {pasta_destino}")
        return

    for arquivo in smbclient.listdir(destino_principal):
        caminho_origem = montar_caminho_smb(destino_principal, arquivo)

        if smbclient.path.isdir(caminho_origem):
            continue

        if any(padrao.match(arquivo) for padrao in padroes):
            print(f"Mantido: {arquivo}")
            continue

        caminho_destino = montar_caminho_smb(pasta_destino, arquivo)
        try:
            smbclient.rename(caminho_origem, caminho_destino)
            print(f"Movido: {arquivo} -> {pasta_destino}")
        except Exception as erro:
            print(f"Falha ao mover {arquivo}: {erro}")
