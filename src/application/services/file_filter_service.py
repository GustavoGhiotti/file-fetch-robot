import re
from re import Pattern


def compilar_padroes(padroes: list[str]) -> list[Pattern]:
    """Transforma textos em padroes de busca.

    Recebe:
        padroes: Lista de textos com regras de nome de arquivo.

    Retorna:
        Lista de padroes prontos para comparar com nomes de arquivos.
    """
    return [re.compile(padrao, re.IGNORECASE) for padrao in padroes]


def nome_corresponde_a_padroes(nome_arquivo: str, padroes: list[Pattern]) -> bool:
    """Verifica se o nome do arquivo combina com algum padrao.

    Recebe:
        nome_arquivo: Nome do arquivo analisado.
        padroes: Lista de padroes ja preparados.

    Retorna:
        True se o nome combinar com algum padrao.
        False se nao combinar.
    """
    return any(padrao.match(nome_arquivo) for padrao in padroes)


def filtrar_por_padroes(arquivos: list[str], padroes: list[Pattern]) -> list[str]:
    """Filtra uma lista de arquivos usando padroes de nome.

    Recebe:
        arquivos: Lista com nomes de arquivos.
        padroes: Lista de padroes aceitos.

    Retorna:
        Lista somente com os arquivos que combinam com os padroes.
    """
    return [
        arquivo
        for arquivo in arquivos
        if nome_corresponde_a_padroes(arquivo, padroes)
    ]