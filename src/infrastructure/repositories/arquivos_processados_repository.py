"""Repositorio duravel de arquivos ja processados por assinatura.

Guarda a assinatura remota (nome|tamanho|mtime) de cada arquivo transferido
para que a deduplicacao nao dependa do manifesto em disco nem do arquivo
continuar existindo no destino de producao.
"""

import pyodbc

from src.infrastructure.config.settings import obter_config_logs


NOME_TABELA = "ROBO_ARQUIVO_PROCESSADO"


class ArquivosProcessadosRepository:
    """Persiste e consulta assinaturas de arquivos ja processados."""

    def __init__(self, config_db: dict | None = None):
        """Guarda a configuracao do banco de logs."""
        self.config_db = config_db or obter_config_logs()

    def garantir_tabela(self) -> None:
        """Cria a tabela de controle caso ela ainda nao exista."""
        query = f"""
            IF NOT EXISTS (
                SELECT 1 FROM sys.tables WHERE name = '{NOME_TABELA}'
            )
            BEGIN
                CREATE TABLE dbo.{NOME_TABELA} (
                    ID BIGINT IDENTITY(1,1) PRIMARY KEY,
                    ROBO_NOME VARCHAR(100) NOT NULL,
                    NOME_ORIGINAL VARCHAR(400) NOT NULL,
                    NOME_DESTINO VARCHAR(400) NULL,
                    ASSINATURA VARCHAR(600) NOT NULL,
                    TAMANHO BIGINT NULL,
                    MTIME_REMOTO BIGINT NULL,
                    SHA256 VARCHAR(64) NULL,
                    PROCESSADO_EM DATETIME NOT NULL DEFAULT GETDATE(),
                    HOSTNAME VARCHAR(200) NULL,
                    PID INT NULL
                );
                CREATE INDEX IX_{NOME_TABELA}_ROBO_ASSIN
                    ON dbo.{NOME_TABELA} (ROBO_NOME, ASSINATURA);
            END
        """
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(query)
            conexao.commit()

    def listar_assinaturas(self, robo_nome: str) -> set[str]:
        """Retorna o conjunto de assinaturas ja processadas por um robo."""
        query = f"""
            SELECT ASSINATURA
            FROM dbo.{NOME_TABELA}
            WHERE ROBO_NOME = ?
        """
        return self._consultar_assinaturas(query, robo_nome)

    def listar_assinaturas_do_dia(self, robo_nome: str) -> set[str]:
        """Retorna as assinaturas registradas HOJE por um robo.

        Usado para deduplicar apenas dentro do dia: se o arquivo do dia ja foi
        processado com a mesma assinatura (nome|tamanho|mtime), e ignorado; se
        foi modificado ao longo do dia, a assinatura muda e ele volta a entrar.
        """
        query = f"""
            SELECT ASSINATURA
            FROM dbo.{NOME_TABELA}
            WHERE ROBO_NOME = ?
              AND CAST(PROCESSADO_EM AS DATE) = CAST(GETDATE() AS DATE)
        """
        return self._consultar_assinaturas(query, robo_nome)

    def _consultar_assinaturas(self, query: str, robo_nome: str) -> set[str]:
        """Executa uma consulta de assinaturas e devolve o conjunto."""
        assinaturas = set()
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(query, robo_nome)
            for row in cursor.fetchall():
                assinatura = str(row[0] or "").strip()
                if assinatura:
                    assinaturas.add(assinatura)
        return assinaturas

    def registrar(
        self,
        robo_nome: str,
        nome_original: str,
        assinatura: str,
        tamanho: int | None,
        mtime_remoto: int | None,
        nome_destino: str | None = None,
        sha256: str | None = None,
        hostname: str | None = None,
        pid: int | None = None,
    ) -> None:
        """Insere uma assinatura de arquivo processado de forma duravel."""
        query = f"""
            INSERT INTO dbo.{NOME_TABELA} (
                ROBO_NOME,
                NOME_ORIGINAL,
                NOME_DESTINO,
                ASSINATURA,
                TAMANHO,
                MTIME_REMOTO,
                SHA256,
                HOSTNAME,
                PID
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                query,
                robo_nome,
                nome_original,
                nome_destino,
                assinatura,
                tamanho,
                mtime_remoto,
                sha256,
                hostname,
                pid,
            )
            conexao.commit()

    def _conectar(self):
        """Abre conexao com o banco de logs."""
        return pyodbc.connect(
            "DRIVER=SQL SERVER;"
            f"SERVER={self.config_db['ipServidor']};"
            f"DATABASE={self.config_db['banco']};"
            f"UID={self.config_db['usuario']};"
            f"PWD={self.config_db['senha']};"
            "TrustServerCertificate=YES"
        )
