from typing import Protocol
from src.domain.models.credencial_remota import CredencialRemota


class CredentialsRepository(Protocol):
    """
    define como uma classe deve buscar credenciais
    """

    def obter_credencial(self, id_cedente: int) -> CredencialRemota:
        """
        busca a credencial de conexao de um cliente

        Recebe:
            id_cedente: codigo do cliente ou carteira

        Retorna: 
            dados de conexao encontrados
        """