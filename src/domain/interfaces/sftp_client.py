"""Compatibilidade com o contrato antigo de SFTP.

Use RemoteFileClient nos novos codigos.
"""

from src.domain.interfaces.remote_file_client import RemoteFileClient


ISFTPClient = RemoteFileClient
