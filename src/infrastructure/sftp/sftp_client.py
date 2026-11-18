"""Cliente SFTP usado para listar, abrir e consultar arquivos."""

from datetime import date, datetime, timedelta
import os
import re
import stat
from time import sleep

from paramiko import AutoAddPolicy, RSAKey, SSHClient


class SFTPClient:
    """Representa uma conexao SFTP."""

    def __init__(self, hostname: str, user: str, port: int, password=None, key_file=None):
        """Cria o cliente SFTP e conecta no servidor."""
        self.hostname = hostname
        self.user = user
        self.port = port
        self.password = password
        self.key_file = key_file
        self._ssh = None
        self._sftp = None
        self._connect()

    def _connect(self) -> None:
        """Tenta conectar no SFTP algumas vezes."""
        pkey = RSAKey.from_private_key_file(self.key_file) if self.key_file else None

        for tentativa in range(5):
            try:
                ssh = SSHClient()
                ssh.set_missing_host_key_policy(AutoAddPolicy())
                ssh.connect(
                    hostname=self.hostname,
                    username=self.user,
                    password=self.password,
                    port=self.port,
                    pkey=pkey,
                    look_for_keys=False,
                    allow_agent=False,
                )
                self._ssh = ssh
                self._sftp = ssh.open_sftp()
                self._ssh.get_transport().set_keepalive(7)
                return
            except Exception as erro:
                print(f"Falha SFTP tentativa {tentativa + 1}/5: {erro}")
                sleep(3)

        raise ConnectionError("Nao foi possivel conectar ao SFTP.")

    def listar_arquivos(self, caminho: str, extensao_arquivo=None, nome_esperado=None) -> list[str]:
        """Lista arquivos do SFTP filtrando por extensao e nome."""
        extensoes = _normalizar_extensoes(extensao_arquivo)
        arquivos = []

        for item in self._sftp.listdir_attr(caminho):
            if not stat.S_ISREG(item.st_mode):
                continue

            nome = item.filename

            if extensoes and os.path.splitext(nome)[1].lower() not in extensoes:
                continue

            if nome_esperado and not _nome_corresponde(nome, nome_esperado):
                continue

            arquivos.append(nome)

        return arquivos

    def listar_arquivos_por_data_modificacao(
        self,
        caminho: str,
        extensao_arquivo=None,
        nome_esperado=None,
        data_referencia: date | None = None,
    ) -> list[dict]:
        """Lista arquivos do SFTP por data de modificacao."""
        extensoes = _normalizar_extensoes(extensao_arquivo)
        data_base = data_referencia or date.today() - timedelta(days=2)
        arquivos = []

        for item in self._sftp.listdir_attr(caminho):
            if not stat.S_ISREG(item.st_mode):
                continue

            nome = item.filename
            extensao = os.path.splitext(nome)[1].lower()

            if extensoes and extensao not in extensoes:
                continue

            if nome_esperado and not _nome_corresponde(nome, nome_esperado):
                continue

            data_modificacao = date.fromtimestamp(item.st_mtime)
            if data_modificacao != data_base:
                continue

            arquivos.append(
                {
                    "nome": nome,
                    "tamanho": item.st_size,
                    "mtime": int(item.st_mtime),
                    "modificado_em": datetime.fromtimestamp(item.st_mtime),
                }
            )

        return arquivos

    def abrir_arquivo(self, caminho: str, modo: str = "rb"):
        """Abre um arquivo no SFTP."""
        return self._sftp.open(caminho, modo)

    def stat(self, caminho: str):
        """Busca informacoes de um arquivo no SFTP."""
        return self._sftp.stat(caminho)

    def fechar(self) -> None:
        """Fecha a conexao SFTP."""
        if self._sftp:
            self._sftp.close()
        if self._ssh:
            self._ssh.close()

    def reconect(self) -> None:
        """Reconecta no SFTP usando os mesmos dados."""
        self.fechar()
        self._connect()


def _normalizar_extensoes(extensao_arquivo) -> list[str]:
    """Transforma extensoes em lista padronizada."""
    if extensao_arquivo is None:
        return []
    if isinstance(extensao_arquivo, str):
        return [extensao_arquivo.lower()]
    return [ext.lower() for ext in extensao_arquivo if isinstance(ext, str) and ext]


def _nome_corresponde(nome_arquivo: str, nome_esperado) -> bool:
    """Verifica se o nome combina com string, regex ou lista de regex."""
    if isinstance(nome_esperado, re.Pattern):
        return bool(nome_esperado.match(nome_arquivo))
    if isinstance(nome_esperado, list):
        return any(_nome_corresponde(nome_arquivo, padrao) for padrao in nome_esperado)
    if isinstance(nome_esperado, str):
        return nome_arquivo == nome_esperado
    return True
