from src.infrastructure.config.env import obter_variavel


def obter_config_banco_66(banco: str = "DB_NAME") -> dict:
    """
    monta a configuracao do banco do servidor 66

    Recebe:
        banco: nome do banco que sera usado

    Retorna:
        dicionario com servidor, banco, usuario e senha
    """

    return {
        "ipServidor": obter_variavel("DB_71"),
        "banco": banco,
        "usuario": obter_variavel("DB_USER"),
        "senha": obter_variavel("DB_SENHA"),
    }


def obter_config_logs() -> dict:
    """
    monta a configuracao do banco de logs dos robos

    Retorna:
        dicionario com servidor, banco, usuario e senha
    """

    return {
        "ipServidor": _obter_variavel_com_fallback("LOG_DB_SERVER", obter_variavel("DB_66")),
        "banco": _obter_variavel_com_fallback("LOG_DB_NAME", "LOGS_ROBOS"),
        "usuario": _obter_variavel_com_fallback("LOG_DB_USER", obter_variavel("DB_USER")),
        "senha": _obter_variavel_com_fallback("LOG_DB_SENHA", obter_variavel("DB_SENHA")),
    }


def _obter_variavel_com_fallback(nome: str, fallback: str) -> str:
    """
    busca uma variavel e usa fallback quando ela nao existe ou esta vazia

    Recebe:
        nome: nome da variavel no .env
        fallback: valor usado quando a variavel estiver vazia

    Retorna:
        valor final para uso na configuracao
    """
    valor = obter_variavel(nome, obrigatoria=False)
    return valor.strip() if valor and valor.strip() else fallback


def modo_teste_ativo() -> bool:
    """
    verifica se o modo de teste esta ativo

    Retorna:
        True quando MODO_TESTE estiver como true, 1, sim ou yes
    """
    valor = obter_variavel("MODO_TESTE", obrigatoria=False, padrao="false")
    return str(valor).strip().lower() in {"true", "1", "sim", "s", "yes"}


def obter_diretorio_teste_saida() -> str | None:
    """
    busca o diretorio usado para saida em modo de teste

    Retorna:
        caminho de teste quando estiver configurado
    """
    return obter_variavel("DIRETORIO_TESTE_SAIDA", obrigatoria=False)


def resolver_destino_execucao(destino_real: str, robo_nome: str | None = None) -> str:
    """
    resolve o destino final considerando o modo de teste

    Recebe:
        destino_real: caminho original de producao
        robo_nome: nome do robo. Mantido apenas para compatibilidade.

    Retorna:
        destino real em producao ou exatamente o destino de teste quando MODO_TESTE=true
    """
    if not modo_teste_ativo():
        return destino_real

    destino_teste = obter_diretorio_teste_saida()
    if not destino_teste:
        raise ValueError("MODO_TESTE=true, mas DIRETORIO_TESTE_SAIDA nao foi configurado.")

    return destino_teste


def obter_config_servidor_64() -> dict:
    """
    monta a configuracao do servidor SMB 64

    Retorna:
        dicionario com servidor, usuario e senha
    """

    return {
        "ipServidor": obter_variavel("SERVER_64"),
        "usuario": obter_variavel("SERVER_USER64"),
        "senha": obter_variavel("SERVER_SENHA64"),
    }


def obter_config_servidor_71() -> dict:
    """
    monta a configuracao do servidor SMB 71

    Retorna:
        dicionario com servidor, usuario e senha
    """

    return {
        "ipServidor": obter_variavel("SERVER_71"),
        "usuario": obter_variavel("SERVER_USER"),
        "senha": obter_variavel("SERVER_SENHA"),
    }


def obter_config_servidor_72() -> dict:
    """
    monta a configuracao do servidor SMB 72

    Retorna:
        dicionario com servidor, usuario e senha
    """

    return {
        "ipServidor": obter_variavel("SERVER_72"),
        "usuario": obter_variavel("SERVER_USER_72"),
        "senha": obter_variavel("SERVER_SENHA_72"),
    }


def obter_config_servidor(numero_servidor: str) -> dict:
    """
    escolhe a configuracao SMB pelo numero do servidor

    Recebe:
        numero_servidor: numero do servidor, como "64", "71" ou "72"

    Retorna:
        configuracao do servidor escolhido
    """
    configs = {
        "64": obter_config_servidor_64,
        "71": obter_config_servidor_71,
        "72": obter_config_servidor_72,
    }

    if numero_servidor not in configs:
        raise ValueError(f"Servidor SMB nao configurado: {numero_servidor}")

    return configs[numero_servidor]()
