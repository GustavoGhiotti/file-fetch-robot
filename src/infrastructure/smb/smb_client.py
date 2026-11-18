"""Cliente SMB usado para acessar pastas de rede."""

from typing import BinaryIO

import smbclient


class SMBClient:
    """Representa uma conexao com servidor SMB."""

    def __init__(self, servidor: str, usuario: str, senha: str):
        """Guarda os dados de conexao do SMB."""
        self.servidor = servidor
        self.usuario = usuario
        self.senha = senha

    def conectar(self) -> None:
        """Abre a sessao SMB."""
        smbclient.register_session(
            server=self.servidor,
            username=self.usuario,
            password=self.senha,
        )

    def listar_arquivos(self, caminho: str) -> list[str]:
        """Lista os arquivos de uma pasta SMB."""
        arquivos = []

        for item in smbclient.scandir(caminho):
            if item.is_file():
                arquivos.append(item.name)

        return arquivos

    def abrir_arquivo(self, caminho: str, modo: str = "rb") -> BinaryIO:
        """Abre um arquivo no SMB."""
        return smbclient.open_file(caminho, mode=modo)

    def gerar_caminho_destino(self, caminho: str) -> BinaryIO:
        """Abre um arquivo SMB para escrita."""
        return smbclient.open_file(caminho, mode="wb")

    def existe(self, caminho: str) -> bool:
        """Verifica se um caminho existe no SMB."""
        return smbclient.path.exists(caminho)

    def remover(self, caminho: str) -> None:
        """Remove um arquivo do SMB."""
        smbclient.remove(caminho)

    def mover(self, origem: str, destino: str) -> None:
        """Move ou renomeia um arquivo no SMB."""
        smbclient.rename(origem, destino)
