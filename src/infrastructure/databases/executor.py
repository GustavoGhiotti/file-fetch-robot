import pyodbc
from typing import List

class Conexao:
    def __init__(self, ipServidor:str, banco:str, usuario:str, senha:str):
        self.__ipServidor = ipServidor
        self.__banco = banco
        self.__usuario = usuario
        self.__senha = senha

    def obter_conexao(self) -> pyodbc.Connection: 
        return pyodbc.connect("DRIVER=SQL SERVER;"
                              f"SERVER={self.__ipServidor};"
                              f"DATABASE={self.__banco};"
                              f"UID={self.__usuario};"
                              f"PWD={self.__senha};"
                              "TrustServerCertificate=YES"
                              )

class Executor(Conexao):
    def __init__(self, ipServidor:str, banco:str, usuario:str, senha:str):
        super().__init__(ipServidor, banco, usuario, senha)


    def executar_query(self,*, query:str, parametros:list, fetch:str = None) -> List[pyodbc.Row] | None:
        try:
            conexao = self.obter_conexao()
            cursor = conexao.cursor()
            cursor.execute(query, parametros)
            
            if fetch == "one":
                colunas = [coluna[0] for coluna in cursor.description]
                dados = cursor.fetchone()
                return dict(zip(colunas,  dados)) if dados else None

            elif fetch == "all":
                colunas = [coluna[0] for coluna in cursor.description]
                return [dict(zip(colunas,dados)) for dados in cursor.fetchall()] 

            else:
                conexao.commit()

        except pyodbc.Error as e:
            print(f"Erro no banco: {e}")

        finally:
            conexao.close()
