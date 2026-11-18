"""Cliente FTP usado para listar, abrir, enviar e mover arquivos."""

from datetime import datetime
from ftplib import FTP, all_errors, error_perm
from io import BytesIO
import os
from time import sleep


class FTPClient:
    """Representa uma conexao FTP."""

    def __init__(
        self,
        hostname: str,
        user: str,
        password: str,
        port: int = 21,
        passive: bool = True,
    ):
        """Cria o cliente FTP e conecta no servidor."""
        self.hostname = hostname
        self.user = user
        self.password = password
        self.port = port
        self.passive = passive
        self._ftp = None
        self._connect()

    def _connect(self) -> None:
        """Tenta conectar no FTP algumas vezes."""
        for tentativa in range(5):
            try:
                ftp = FTP()
                ftp.connect(self.hostname, self.port, timeout=15)
                ftp.login(self.user, self.password)
                ftp.set_pasv(self.passive)
                self._ftp = ftp
                return
            except all_errors as erro:
                print(f"Falha FTP tentativa {tentativa + 1}/5: {erro}")
                sleep(3)

        raise ConnectionError("Nao foi possivel conectar ao FTP.")

    def listar_arquivos(
        self,
        caminho: str,
        extensao_arquivo: str | tuple[str, ...],
        nome_esperado=None,
        dia_referencia: str | None = None,
    ) -> list[str]:
        """Lista arquivos do FTP filtrando por extensao, nome e data."""
        try:
            self._ftp.cwd(caminho)
            arquivos = self._ftp.nlst()
        except error_perm as erro:
            print(f"Diretorio remoto nao encontrado: {caminho} ({erro})")
            return []
        except Exception as erro:
            print(f"Erro ao listar arquivos FTP: {erro}")
            return []

        extensoes = _normalizar_extensoes(extensao_arquivo)
        arquivos_filtrados = []

        for arquivo in arquivos:
            nome = os.path.basename(arquivo)

            if extensoes and not nome.lower().endswith(extensoes):
                continue

            if nome_esperado and not _nome_corresponde(nome, nome_esperado):
                continue

            if dia_referencia and self._data_modificacao(nome) != dia_referencia:
                continue

            arquivos_filtrados.append(nome)

        return arquivos_filtrados

    def listar_arquivos_mes(
        self,
        caminho: str,
        extensao_arquivo: str | tuple[str, ...],
        mes_referencia: str | None = None,
        nome_esperado=None,
    ) -> list[str]:
        """Lista arquivos do FTP filtrando pelo mes de modificacao."""
        try:
            self._ftp.cwd(caminho)
            arquivos = self._ftp.nlst()
        except error_perm as erro:
            print(f"Diretorio remoto nao encontrado: {caminho} ({erro})")
            return []

        extensoes = _normalizar_extensoes(extensao_arquivo)
        arquivos_filtrados = []

        for arquivo in arquivos:
            nome = os.path.basename(arquivo)

            if extensoes and not nome.lower().endswith(extensoes):
                continue

            data_modificacao = self._data_modificacao(nome)
            if mes_referencia and not data_modificacao.startswith(mes_referencia):
                continue

            if nome_esperado and not _nome_corresponde(nome, nome_esperado):
                continue

            arquivos_filtrados.append(nome)

        return arquivos_filtrados

    def abrir_arquivo(self, caminho: str, modo: str = "rb") -> BytesIO:
        """Abre um arquivo FTP e devolve o conteudo em memoria."""
        buffer = BytesIO()
        self._ftp.retrbinary(f"RETR {caminho}", buffer.write)
        buffer.seek(0)
        return buffer

    def mover_arquivo(self, origem: str, destino: str) -> None:
        """Move um arquivo dentro do FTP."""
        self._ftp.rename(origem, destino)

    def fechar(self) -> None:
        """Fecha a conexao FTP."""
        if self._ftp:
            self._ftp.quit()

    def _data_modificacao(self, nome_arquivo: str) -> str:
        """Busca a data de modificacao de um arquivo no FTP."""
        try:
            resposta = self._ftp.sendcmd(f"MDTM {nome_arquivo}")
            data_str = resposta[4:].split(".")[0]
            return datetime.strptime(data_str, "%Y%m%d%H%M%S").strftime("%Y%m%d")
        except Exception:
            return ""


def _normalizar_extensoes(extensao_arquivo: str | tuple[str, ...] | None) -> tuple[str, ...]:
    """Transforma extensoes em uma tupla padronizada."""
    if not extensao_arquivo:
        return tuple()
    if isinstance(extensao_arquivo, str):
        return (extensao_arquivo.lower(),)
    return tuple(extensao.lower() for extensao in extensao_arquivo)


def _nome_corresponde(nome_arquivo: str, nome_esperado) -> bool:
    """Verifica se o nome combina com string, regex ou lista de regex."""
    if isinstance(nome_esperado, str):
        return nome_arquivo == nome_esperado
    if isinstance(nome_esperado, list):
        return any(padrao.match(nome_arquivo) for padrao in nome_esperado)
    return bool(nome_esperado.match(nome_arquivo))
