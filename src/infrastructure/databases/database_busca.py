from .executor import Executor, Conexao

class Busca_Arquivos:
    def __init__(self, conexao:Conexao):
        self.executor = Executor(**conexao)

    def obter_credencial(self, id_cedente:int) -> list:
        query = """
                    SELECT
                        NM_CEDENTE, 
                        HOSTNAME,
                        USUARIO,
                        SENHA,
                        PORTA_HOST,
                        ORIGEM_CARGA,
                        DESTINO_CARGA
                    FROM Carga.TB_CONEXAO_SFTP WITH(NOLOCK)
                    WHERE ID_CEDENTE = ?
                """
        parametros = [id_cedente]
        
        return self.executor.executar_query(query=query, parametros=parametros, fetch="one")
