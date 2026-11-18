from typing import Protocol, BinaryIO


class RemoteFileClient(Protocol):
    """
    Define o comportamento minimo de uma origem de arquivos
    """

    def listar_arquivos(self, caminho:str, extensao_arquivo: str, nome_esperado = None) -> list[str]:
        """
        Lista arquivos disponiveis em uma pasta remota

        Recebe:
            caminho: pasta onde os arquivos serao procurados
            extensao_arquivo: extensao esperada dos arquivos
            nome_esperado: nome ou padrao esperado para filtrar arquivos

        Retorna:
            Lista com os nome dos arquivos encontrados
        """


    def abrir_arquivo(self, caminho: str, modo: str = "rb") -> BinaryIO:
        """
        abre um arquivo remoto para leitura ou escrita

        Recebe:
            caminho: caminho completo do arquivo remoto
            modo: modo de abertura, por exemplo "rb" para leitura em bytes

        Retorna:
            arquivo aberto
        """
