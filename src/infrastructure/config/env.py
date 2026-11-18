import os
from dotenv import load_dotenv


load_dotenv()


def obter_variavel(nome: str, obrigatoria: bool = True, padrao: str | None = None) -> str | None:
    """
    Busca uma variavel de ambiente

    Recebe:
        nome: nome da variavel no arquivo .env
        obrigatoria: indica se a variavel precisa existir
        padrao: valor usado caso a variavel nao exista

    Retorna:
        valor da variavel encontrada

    Erro:
        gera erro se a variavel for obrigatoria e nao existir
    """

    valor = os.getenv(nome, padrao)

    if obrigatoria and not valor:
        raise ValueError(f"variavel de ambiente nao encontrada: {nome}")
    
    return valor