"""Postagem dos retornos Upsilon gerados pela VCOM."""

from datetime import date
import os
import re
import shutil
from time import sleep

import smbclient

from src.application.services.transfer_service import montar_caminho_remoto, montar_caminho_smb
from src.infrastructure.config.env import obter_variavel
from src.infrastructure.config.settings import obter_config_banco_66, obter_config_servidor_71
from src.infrastructure.repositories.credentials_repository import DatabaseCredentialsRepository
from src.infrastructure.sftp.sftp_client import SFTPClient
from src.infrastructure.smb.smb_client import SMBClient
from src.shared.transfer_log import criar_item_transferencia


TAMANHO_BUFFER = 1024 * 1024 * 8
ID_CEDENTE_ORIGEM_VCOM = 1000
ID_CEDENTE_DESTINO_UPSILON = 1002
PREFIXOS_ESPERADOS = (
    "ACME_ACIONAMENTOS",
    "ACME_PHONE",
    "ACME_ADRESS",
    "ACME_ADDRESS",
    "ACMEUHC_ACIONAMENTOS",
    "ACMEUHC_PHONE",
    "ACMEUHC_ADRESS",
    "ACMEUHC_ADDRESS",
)
PADRAO_ARQUIVO_RETORNO = re.compile(
    r"^(?P<data>\d{8})_(?P<hora>\d{6})_(?P<nome>.+)$",
    re.IGNORECASE,
)
NOMES_MESES = {
    "01": "Jan",
    "02": "Fev",
    "03": "Março",
    "04": "Abril",
    "05": "Maio",
    "06": "Junho",
    "07": "Julho",
    "08": "Agosto",
    "09": "Setembro",
    "10": "Outubro",
    "11": "Novembro",
    "12": "Dezembro",
}


def executar_retorno_upsilon() -> list[dict]:
    """Copia retornos da VCOM, salva backup e posta no SFTP Upsilon."""
    repositorio_credenciais = DatabaseCredentialsRepository(obter_config_banco_66("DB_DESENVOLVIMENTO"))
    origem_sftp = _criar_sftp_por_id_cedente(repositorio_credenciais, ID_CEDENTE_ORIGEM_VCOM)
    destino_sftp = _criar_sftp_por_id_cedente(repositorio_credenciais, ID_CEDENTE_DESTINO_UPSILON)
    servidor_backup = _criar_servidor_backup()

    pasta_origem = obter_variavel("VCOM_RETORNO_DIRETORIO_ORIGEM", padrao="/Exportacao")
    pasta_destino = obter_variavel(
        "UPSILON_RETORNO_DIRETORIO_DESTINO",
        padrao="/Remessa/RETORNO_CYBER",
    )
    pasta_backup = obter_variavel(
        "UPSILON_RETORNO_DIRETORIO_BACKUP",
        padrao=r"\\10.0.0.71\Automacao\Arquivo retorno Upsilon",
    )
    data_referencia = _obter_data_referencia()

    try:
        _garantir_pasta_backup(pasta_backup)
        arquivos = origem_sftp.listar_arquivos(pasta_origem)
        arquivos_processados = []

        for arquivo_origem in arquivos:
            nome_destino = normalizar_nome_retorno(arquivo_origem, data_referencia)
            if not nome_destino:
                continue

            caminho_origem = montar_caminho_remoto(pasta_origem, arquivo_origem)
            caminho_backup = montar_caminho_backup(pasta_backup, nome_destino)
            caminho_destino = montar_caminho_remoto(pasta_destino, nome_destino)

            _aguardar_arquivo_estavel(origem_sftp, caminho_origem)
            tamanho_origem = origem_sftp.stat(caminho_origem).st_size
            backup_atualizado = _smb_possui_arquivo(servidor_backup, caminho_backup, tamanho_origem)
            destino_atualizado = _sftp_possui_arquivo(destino_sftp, caminho_destino, tamanho_origem)

            if backup_atualizado and destino_atualizado:
                print(f"Arquivo ja processado no backup e SFTP destino: {nome_destino}")
                continue

            if not backup_atualizado:
                _garantir_pasta_backup(_obter_pasta_smb(caminho_backup))
                _copiar_sftp_para_smb(origem_sftp, caminho_origem, servidor_backup, caminho_backup)

            if not destino_atualizado:
                _copiar_sftp_para_sftp(origem_sftp, caminho_origem, destino_sftp, caminho_destino)
                _validar_tamanho_destino(origem_sftp, caminho_origem, destino_sftp, caminho_destino)

            observacao = "Nome ajustado automaticamente." if arquivo_origem != nome_destino else None
            arquivos_processados.append(
                criar_item_transferencia(
                    arquivo=nome_destino,
                    origem=caminho_origem,
                    destino=caminho_destino,
                    observacao=_montar_observacao(observacao, caminho_backup),
                )
            )
            print(f"Arquivo enviado: {arquivo_origem} -> {nome_destino}")

        if not arquivos_processados:
            print("Nenhum arquivo de retorno Upsilon encontrado para envio.")

        return arquivos_processados
    finally:
        origem_sftp.fechar()
        destino_sftp.fechar()


def normalizar_nome_retorno(nome_arquivo: str, data_referencia: str | None = None) -> str | None:
    """Retorna o nome canonico esperado pela Upsilon para a data informada."""
    nome_base, extensao = os.path.splitext(nome_arquivo)
    arquivo_retorno = PADRAO_ARQUIVO_RETORNO.match(nome_base)

    if not arquivo_retorno:
        return None

    if data_referencia and arquivo_retorno.group("data") != data_referencia:
        return None

    data_arquivo = arquivo_retorno.group("data")
    hora_arquivo = arquivo_retorno.group("hora")
    nome_retorno_upper = arquivo_retorno.group("nome").upper()

    for prefixo in PREFIXOS_ESPERADOS:
        if nome_retorno_upper.startswith(prefixo):
            return f"{data_arquivo}_{hora_arquivo}_{prefixo}_1_in{extensao}"

    return None


def montar_caminho_backup(pasta_backup: str, nome_arquivo: str) -> str:
    """Monta o caminho SMB final separando Upsilon, UHC e mes."""
    nome_base, _ = os.path.splitext(nome_arquivo)
    arquivo_retorno = PADRAO_ARQUIVO_RETORNO.match(nome_base)

    if not arquivo_retorno:
        raise ValueError(f"Nome de retorno fora do padrao esperado: {nome_arquivo}")

    nome_retorno_upper = arquivo_retorno.group("nome").upper()
    mes = _obter_nome_mes(arquivo_retorno.group("data"))
    eh_uhc = "ACMEUHC" in nome_retorno_upper

    pasta_cliente = "Upsilon UHC" if eh_uhc else "Upsilon"
    pasta_mes = f"{mes} UHC" if eh_uhc else mes
    pasta_destino = montar_caminho_smb(montar_caminho_smb(pasta_backup, pasta_cliente), pasta_mes)

    return montar_caminho_smb(pasta_destino, nome_arquivo)


def _obter_nome_mes(data_arquivo: str) -> str:
    """Retorna o nome da pasta do mes a partir de uma data AAAAMMDD."""
    mes = data_arquivo[4:6]
    if mes not in NOMES_MESES:
        raise ValueError(f"Mes invalido no nome do arquivo: {data_arquivo}")
    return NOMES_MESES[mes]


def _obter_pasta_smb(caminho_smb: str) -> str:
    """Retorna a pasta de um caminho SMB."""
    return caminho_smb.rsplit("\\", 1)[0]


def _obter_data_referencia() -> str:
    """Busca a data do arquivo no formato AAAAMMDD."""
    data_configurada = obter_variavel(
        "UPSILON_RETORNO_DATA_REFERENCIA",
        obrigatoria=False,
    )

    if data_configurada:
        data_configurada = data_configurada.strip()
        if not re.fullmatch(r"\d{8}", data_configurada):
            raise ValueError("UPSILON_RETORNO_DATA_REFERENCIA deve estar no formato AAAAMMDD.")
        return data_configurada

    return date.today().strftime("%Y%m%d")


def _criar_sftp_por_id_cedente(
    repositorio_credenciais: DatabaseCredentialsRepository,
    id_cedente: int,
) -> SFTPClient:
    """Busca credencial no banco e cria a conexao SFTP."""
    credencial = repositorio_credenciais.obter_credencial(id_cedente)
    chave_privada = _resolver_chave_privada(credencial.senha)
    return SFTPClient(
        hostname=credencial.hostname,
        user=credencial.usuario,
        password=None if chave_privada else credencial.senha,
        port=credencial.porta,
        key_file=chave_privada,
    )


def _resolver_chave_privada(chave_privada: str | None) -> str | None:
    """Resolve chave privada quando o valor aponta para um arquivo existente."""
    if not chave_privada:
        return None

    if os.path.exists(chave_privada):
        return chave_privada

    caminho_senhas = os.path.join(os.getcwd(), "senhas", chave_privada)
    if os.path.exists(caminho_senhas):
        return caminho_senhas

    return None


def _criar_servidor_backup() -> SMBClient:
    """Abre sessao SMB no servidor 71 para gravar a copia local."""
    config = obter_config_servidor_71()
    servidor = SMBClient(config["ipServidor"], config["usuario"], config["senha"])
    servidor.conectar()
    return servidor


def _garantir_pasta_backup(pasta_backup: str) -> None:
    """Cria a pasta de backup se ela ainda nao existir."""
    if not smbclient.path.exists(pasta_backup):
        smbclient.makedirs(pasta_backup)


def _aguardar_arquivo_estavel(cliente_sftp: SFTPClient, caminho_origem: str) -> None:
    """Evita copiar arquivo ainda em escrita no SFTP origem."""
    tamanho_inicial = cliente_sftp.stat(caminho_origem).st_size
    sleep(2)
    tamanho_final = cliente_sftp.stat(caminho_origem).st_size

    if tamanho_inicial != tamanho_final:
        raise RuntimeError(f"Arquivo ainda em escrita no SFTP origem: {caminho_origem}")


def _copiar_sftp_para_smb(
    origem_sftp: SFTPClient,
    caminho_origem: str,
    servidor_backup: SMBClient,
    caminho_backup: str,
) -> None:
    """Copia o arquivo da origem SFTP para o backup SMB."""
    with origem_sftp.abrir_arquivo(caminho_origem, "rb") as origem:
        with servidor_backup.abrir_arquivo(caminho_backup, "wb") as destino:
            shutil.copyfileobj(origem, destino, length=TAMANHO_BUFFER)
            destino.flush()


def _smb_possui_arquivo(servidor_backup: SMBClient, caminho_backup: str, tamanho_origem: int) -> bool:
    """Confere se o backup SMB ja existe com o mesmo tamanho."""
    if not servidor_backup.existe(caminho_backup):
        return False

    try:
        with servidor_backup.abrir_arquivo(caminho_backup, "rb") as arquivo_backup:
            arquivo_backup.seek(0, os.SEEK_END)
            return arquivo_backup.tell() == tamanho_origem
    except Exception:
        return False


def _sftp_possui_arquivo(destino_sftp: SFTPClient, caminho_destino: str, tamanho_origem: int) -> bool:
    """Confere se o SFTP destino ja possui o arquivo com o mesmo tamanho."""
    try:
        return destino_sftp.stat(caminho_destino).st_size == tamanho_origem
    except Exception:
        return False


def _copiar_sftp_para_sftp(
    origem_sftp: SFTPClient,
    caminho_origem: str,
    destino_sftp: SFTPClient,
    caminho_destino: str,
) -> None:
    """Copia o arquivo da origem SFTP para o SFTP da Upsilon."""
    with origem_sftp.abrir_arquivo(caminho_origem, "rb") as origem:
        with destino_sftp.abrir_arquivo(caminho_destino, "wb") as destino:
            shutil.copyfileobj(origem, destino, length=TAMANHO_BUFFER)
            destino.flush()


def _validar_tamanho_destino(
    origem_sftp: SFTPClient,
    caminho_origem: str,
    destino_sftp: SFTPClient,
    caminho_destino: str,
) -> None:
    """Confirma se o arquivo postado ficou com o mesmo tamanho da origem."""
    tamanho_origem = origem_sftp.stat(caminho_origem).st_size
    tamanho_destino = destino_sftp.stat(caminho_destino).st_size

    if tamanho_origem != tamanho_destino:
        raise RuntimeError(
            f"Tamanho divergente apos postagem: {caminho_destino} "
            f"(origem={tamanho_origem}, destino={tamanho_destino})"
        )


def _montar_observacao(observacao: str | None, caminho_backup: str) -> str:
    """Monta a observacao registrada no log."""
    partes = [f"Backup salvo em {caminho_backup}."]
    if observacao:
        partes.insert(0, observacao)
    return " ".join(partes)
