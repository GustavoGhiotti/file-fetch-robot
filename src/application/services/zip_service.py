"""Funcoes para trabalhar com arquivos ZIP em SMB."""

import zipfile

import smbclient


def extrair_zip_smb(caminho_zip: str, pasta_destino: str) -> list[str]:
    """Extrai um ZIP que esta no SMB.

    Recebe:
        caminho_zip: caminho completo do arquivo ZIP.
        pasta_destino: pasta onde os arquivos serao extraidos.

    Retorna:
        Lista com os caminhos completos dos arquivos extraidos.
    """
    arquivos_extraidos = []

    with smbclient.open_file(caminho_zip, mode="rb") as zip_data:
        with zipfile.ZipFile(zip_data) as zip_ref:
            for nome_arquivo in zip_ref.namelist():
                destino_extraido = pasta_destino.rstrip("\\") + "\\" + nome_arquivo

                with smbclient.open_file(destino_extraido, mode="wb") as arquivo_destino:
                    arquivo_destino.write(zip_ref.read(nome_arquivo))

                arquivos_extraidos.append(destino_extraido)
                print(f"Extraido: {nome_arquivo}")

    return arquivos_extraidos


def remover_arquivo_smb(caminho_arquivo: str) -> None:
    """Remove um arquivo no SMB se ele existir.

    Recebe:
        caminho_arquivo: caminho completo do arquivo no SMB.
    """
    if smbclient.path.exists(caminho_arquivo):
        smbclient.remove(caminho_arquivo)
