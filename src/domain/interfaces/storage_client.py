from typing import Protocol, BinaryIO


class StorageClient(Protocol):
    """
    Define o comportamento minimo de um destino de arquivos
    """

    def listar_arquivos(self, caminho:str) -> list[str]:
        """
        lista arquivos existentes em uma pasta de destino

        Recebe: 
            caminho: pasta onde os arquivos serao listados

        Retorna:
            lista com os nomes dos arquivos encontrados
        """

    def gerar_caminho_destino(self, caminho: str) -> BinaryIO:
        """
        abre um caminho de destino para gravacao

        Recebe:
            caminho: caminho completo onde o arquivo sera salvo

        Retorna:
            arquivo aberto para escrita
        """