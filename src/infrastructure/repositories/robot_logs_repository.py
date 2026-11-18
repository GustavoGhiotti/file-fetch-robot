"""Repositorio para salvar logs de execucao dos robos."""

import pyodbc

from src.domain.models.robo_log import RoboLog
from src.infrastructure.config.settings import obter_config_logs


class RobotLogsRepository:
    """Salva logs na base LOGS_ROBOS."""

    def __init__(self, config_db: dict | None = None):
        """Guarda a configuracao do banco de logs."""
        self.config_db = config_db or obter_config_logs()

    def salvar(self, log: RoboLog) -> None:
        """Insere um registro de log no banco."""
        query = """
            INSERT INTO dbo.ROBO_EXECUCAO_LOG (
                ID_EXECUCAO,
                ROBO_NOME,
                SCRIPT_NOME,
                EVENTO_TIPO,
                STATUS,
                MENSAGEM,
                ARQUIVOS,
                CAMINHOS_ORIGEM,
                CAMINHOS_DESTINO,
                DETALHES_JSON,
                DATA_INICIO,
                DATA_FIM,
                DURACAO_SEGUNDOS,
                HOSTNAME,
                USUARIO_WINDOWS,
                PID
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                query,
                str(log.id_execucao),
                log.robo_nome,
                log.script_nome,
                log.evento_tipo,
                log.status,
                log.mensagem,
                log.arquivos,
                log.caminhos_origem,
                log.caminhos_destino,
                log.detalhes_json,
                log.data_inicio,
                log.data_fim,
                log.duracao_segundos,
                log.hostname,
                log.usuario_windows,
                log.pid,
            )
            conexao.commit()

    def listar_arquivos_transferidos(self, robo_nome: str | None = None) -> set[str]:
        """Lista nomes de arquivos ja registrados como transferencia com sucesso.

        Recebe:
            robo_nome: quando informado, filtra somente os logs desse robo.

        Retorna:
            Conjunto com nomes de arquivos em minusculo para comparacao exata.
        """
        filtros = [
            "EVENTO_TIPO = ?",
            "STATUS = ?",
            "ARQUIVOS IS NOT NULL",
        ]
        parametros = ["TRANSFERENCIA", "SUCESSO"]

        if robo_nome:
            filtros.append("ROBO_NOME = ?")
            parametros.append(robo_nome)

        query = f"""
            SELECT ARQUIVOS
            FROM dbo.ROBO_EXECUCAO_LOG
            WHERE {' AND '.join(filtros)}
        """

        arquivos = set()
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(query, *parametros)
            for row in cursor.fetchall():
                for arquivo in str(row[0] or "").split(";"):
                    nome = arquivo.strip()
                    if nome:
                        arquivos.add(nome.lower())

        return arquivos

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
