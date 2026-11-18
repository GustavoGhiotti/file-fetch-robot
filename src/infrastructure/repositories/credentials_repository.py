"""Repositorio para buscar credenciais no banco."""

from src.domain.models.credencial_remota import CredencialRemota
from src.infrastructure.databases.database_busca import Busca_Arquivos


class DatabaseCredentialsRepository:
    """Busca credenciais remotas na tabela de conexao."""

    def __init__(self, config_db: dict):
        """Guarda a configuracao do banco."""
        self._repository = Busca_Arquivos(config_db)

    def obter_credencial(self, id_cedente: int) -> CredencialRemota:
        """Busca credenciais e devolve um modelo padronizado."""
        resultado = self._repository.obter_credencial(id_cedente)

        if not resultado:
            raise ValueError(f"Credencial nao encontrada para id_cedente={id_cedente}")

        return CredencialRemota(
            hostname=resultado["HOSTNAME"],
            usuario=resultado["USUARIO"],
            senha=resultado["SENHA"],
            porta=int(resultado["PORTA_HOST"]),
            nome_cedente=resultado.get("NM_CEDENTE"),
            origem_carga=resultado.get("ORIGEM_CARGA"),
            destino_carga=resultado.get("DESTINO_CARGA"),
        )
