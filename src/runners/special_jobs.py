"""Runners para jobs que possuem regras especificas."""

from datetime import date, datetime, time, timedelta
from email.message import EmailMessage
import csv
import fnmatch
import hashlib
import io
import os
import re
import shutil
import smtplib
import socket
import uuid
import zipfile
from time import sleep

from openpyxl import load_workbook
from paramiko.ssh_exception import SSHException
import smbclient

from src.application.services.csv_service import converter_csv_smb_para_utf8_virgula
from src.application.services.transfer_service import mover_restantes_por_padrao
from src.infrastructure.config.env import obter_variavel
from src.infrastructure.config.settings import (
    obter_config_banco_66,
    obter_config_servidor_64,
    obter_config_servidor_71,
    obter_config_servidor_72,
    resolver_destino_execucao,
)
from src.infrastructure.ftp.ftp_client import FTPClient
from src.infrastructure.repositories.arquivos_processados_repository import ArquivosProcessadosRepository
from src.infrastructure.repositories.credentials_repository import DatabaseCredentialsRepository
from src.infrastructure.repositories.robot_logs_repository import RobotLogsRepository
from src.infrastructure.sftp.sftp_client import SFTPClient
from src.infrastructure.smb.smb_client import SMBClient
from src.shared.transfer_log import criar_item_transferencia
from src.shared.utils.telegram_utils import enviar_telegram


TAMANHO_BUFFER_HASH = 8 * 1024 * 1024
TAMANHO_BUFFER_TRANSFERENCIA = 32 * 1024 * 1024
MAX_TENTATIVAS_TRANSFERENCIA = 5
MAX_TENTATIVAS_ARQUIVO_BLOQUEADO = 5
SEGUNDOS_ESPERA_ARQUIVO_BLOQUEADO = 10


def executar_mu_pagamentos() -> list[str]:
    """Executa o fluxo Mu Pagamentos Pix."""
    arquivos_processados = []
    credencial = _obter_credencial(3)
    origem_busca = credencial.origem_carga
    destino_busca = resolver_destino_execucao(
        r"\\10.0.0.64\arquivos\carga\Mu Cyber\PagamentosPix",
        "mu",
    )
    dia_referencia = date.today().strftime("%Y%m%d")

    ftp = FTPClient(credencial.hostname, credencial.usuario, credencial.senha, credencial.porta)
    smb = _criar_smb(obter_config_servidor_64())

    try:
        arquivos = ftp.listar_arquivos(origem_busca, ".txt", dia_referencia=dia_referencia)
        arquivos_logados = _listar_arquivos_banco_logs("mu")
        for arquivo in arquivos:
            if "RAJADAS_PAGTOS_PIX" not in arquivo:
                continue
            origem = f"{origem_busca}/{arquivo}"
            destino = destino_busca.rstrip("\\") + "\\" + arquivo
            if smb.existe(destino) or arquivo.lower() in arquivos_logados:
                print(f"Arquivo ja processado: {arquivo}")
                continue
            _copiar_ftp_para_smb(ftp, origem, smb, destino)
            ftp.mover_arquivo(origem, f"{origem_busca}/PIX/{arquivo}")
            arquivos_processados.append(criar_item_transferencia(arquivo, origem, destino))
    finally:
        ftp.fechar()

    return arquivos_processados


def executar_mu_retirada() -> list[str]:
    """Executa o fluxo Mu Retirada."""
    arquivos_processados = []
    credencial = _obter_credencial(3)
    origem_base = credencial.origem_carga
    destino_busca = resolver_destino_execucao(
        r"\\10.0.0.71\Automacao\Carga_Mu\Retirada",
        "mu_retirada",
    )
    dia_referencia = date.today().strftime("%Y%m%d")

    ftp = FTPClient(credencial.hostname, credencial.usuario, credencial.senha, credencial.porta)
    smb = _criar_smb(obter_config_servidor_71())

    try:
        arquivos_logados = _listar_arquivos_banco_logs("mu_retirada")
        origem_arquivo = origem_base
        arquivos = ftp.listar_arquivos(origem_arquivo, ".txt", dia_referencia=dia_referencia)
        if not arquivos:
            origem_arquivo = f"{origem_base}/Carga"
            arquivos = ftp.listar_arquivos(origem_arquivo, ".txt", dia_referencia=dia_referencia)

        for arquivo in arquivos:
            if "RET_DISTRIBUICAO_CHI" not in arquivo:
                continue
            origem = f"{origem_arquivo}/{arquivo}"
            destino = destino_busca.rstrip("\\") + "\\" + arquivo
            if smb.existe(destino) or arquivo.lower() in arquivos_logados:
                print(f"Arquivo ja processado: {arquivo}")
                continue
            _copiar_ftp_para_smb(ftp, origem, smb, destino)
            arquivos_processados.append(criar_item_transferencia(arquivo, origem, destino))
    finally:
        ftp.fechar()

    return arquivos_processados


def executar_mu_bat() -> list[str]:
    """Executa o fluxo Mu Batimento."""
    total_arquivos = 0
    nomes_copiados = []
    token = os.getenv("TOKEN")
    chat_id = os.getenv("ID_CHAT")
    credencial = _obter_credencial(3)
    origem_busca = obter_variavel("ORIGEM_MU")
    destino_busca = resolver_destino_execucao(
        obter_variavel("DESTINO_MU"),
        "mu_bat",
    )
    origens = [
        obter_variavel("ORIGEM_MU", obrigatoria=False),
        obter_variavel("ORIGEM_MU2", obrigatoria=False),
    ]

    mes = date.today() - timedelta(days=1)
    mes_referencia = mes.strftime("%Y%m")
    ano_referencia = mes_referencia[:4]
    mes_numero = mes_referencia[4:6]
    padroes = [
        re.compile(fr"^BAT_ACORDO_PGTO_CHI_(?:{mes_referencia}\d{{2}}|\d{{2}}{mes_numero}{ano_referencia}).*\.txt$"),
        re.compile(fr"^BAT_ACORDO_CHI_(?:{mes_referencia}\d{{2}}|\d{{2}}{mes_numero}{ano_referencia}).*\.txt$"),
        re.compile(fr"^BAT_CONTRATOS_CHI_(?:{mes_referencia}\d{{2}}|\d{{2}}{mes_numero}{ano_referencia}).*\.txt$"),
    ]

    ftp = FTPClient(credencial.hostname, credencial.usuario, credencial.senha, credencial.porta)
    smb = _criar_smb(obter_config_servidor_64())

    try:
        arquivos = []
        for origem in origens:
            if origem:
                arquivos.extend(
                    ftp.listar_arquivos_mes(
                        origem,
                        ".txt",
                        mes_referencia=mes_referencia,
                        nome_esperado=padroes,
                    )
                )
        arquivos = list(dict.fromkeys(arquivos))

        if not arquivos:
            print("Nenhum arquivo .txt encontrado para o periodo.")
            return []

        destino_ok = destino_busca.rstrip("\\") + "\\ok"
        processados = smb.listar_arquivos(destino_busca) + smb.listar_arquivos(destino_ok)
        processados.extend(_listar_arquivos_banco_logs("mu_bat"))

        for arquivo in arquivos:
            prefixo = os.path.splitext(arquivo)[0]
            if any(item.lower().startswith(prefixo.lower()) for item in processados):
                print(f"Arquivo ja processado: {prefixo}")
                continue
            origem = f"{origem_busca}/{arquivo}"
            destino = destino_busca.rstrip("\\") + "\\" + arquivo
            _copiar_ftp_para_smb(ftp, origem, smb, destino)
            nomes_copiados.append(criar_item_transferencia(arquivo, origem, destino))
            total_arquivos += 1

        if total_arquivos:
            msg = "Arquivo(s) Mu Batimento:\n" + "\n".join(
                f"Arquivo:\n{item['arquivo']}\n Esta no FTP\n" for item in nomes_copiados
            )
            enviar_telegram(token, chat_id, msg)
    finally:
        ftp.fechar()

    return nomes_copiados


def executar_mu_bsc() -> list[str]:
    """Executa o fluxo Mu BSC."""
    arquivos_processados = []
    credencial = _obter_credencial(3)
    origem_busca = credencial.origem_carga
    destino_busca = resolver_destino_execucao(
        r"\\10.0.0.64\arquivos\carga\Mu Cyber\BSC",
        "mu_bsc",
    )
    destino_drive = r"Z:\Planejamento\MIS OPERACAO\BSC MU"
    data_email = date.today().strftime("%d/%m")
    remetente = os.getenv("EMAIL")
    senha_email = os.getenv("EMAIL_SENHA")

    ftp = FTPClient(credencial.hostname, credencial.usuario, credencial.senha, credencial.porta)
    smb = _criar_smb(obter_config_servidor_64())

    try:
        arquivos = ftp.listar_arquivos(origem_busca, ".xlsx")
        arquivos_logados = _listar_arquivos_banco_logs("mu_bsc")
        for arquivo in arquivos:
            if "BSC_CSF_CICLO_1_Oficial" not in arquivo:
                continue
            origem = f"{origem_busca}/{arquivo}"
            destino = destino_busca.rstrip("\\") + "\\" + arquivo
            if smb.existe(destino) or arquivo.lower() in arquivos_logados:
                print(f"Arquivo ja processado: {arquivo}")
                continue
            _copiar_ftp_para_smb(ftp, origem, smb, destino)
            _enviar_drive_bsc(destino_drive, destino)
            ftp.mover_arquivo(origem, f"{origem_busca}/BSC/{arquivo}")
            _enviar_email_bsc(arquivo, data_email, remetente, senha_email)
            arquivos_processados.append(criar_item_transferencia(arquivo, origem, destino))
    finally:
        ftp.fechar()

    return arquivos_processados


def executar_banco_iota() -> list[str]:
    """Executa o fluxo Banco Iota."""
    arquivos_processados = []
    credencial = _obter_credencial(94)
    origem_busca = obter_variavel("DIRETORIO_SFTP_BANCOIOTA").strip()
    destino_busca = resolver_destino_execucao(
        obter_variavel("DIRETORIO_71_BANCOIOTA").strip(),
        "banco_iota",
    )
    padrao = re.compile(r"^BOLETOS GERADOS ACME.*\.xlsx$", re.IGNORECASE)

    sftp = SFTPClient(credencial.hostname, credencial.usuario, credencial.porta, password=credencial.senha)
    _criar_smb(obter_config_servidor_71())

    try:
        arquivos = sftp.listar_arquivos_por_data_modificacao(origem_busca, ".xlsx", padrao)
        if not arquivos:
            print("Nenhum arquivo .xlsx com modificacao esperada encontrado.")
            return []

        arquivos_logados = _listar_arquivos_banco_logs("banco_iota")
        for arquivo in sorted(arquivos, key=lambda item: (item["mtime"], item["nome"])):
            data_movimentacao = arquivo["modificado_em"]
            nome_destino = _gerar_nome_banco_iota(data_movimentacao)
            destino_arquivo = destino_busca.rstrip("\\") + "\\" + nome_destino
            origem_remota = f"{origem_busca.rstrip('/')}/{arquivo['nome']}"

            if (
                _banco_iota_ja_transferido(destino_busca, data_movimentacao)
                or arquivo["nome"].lower() in arquivos_logados
                or nome_destino.lower() in arquivos_logados
            ):
                print(f"[JA_TRANSFERIDO] Arquivo ja processado: {nome_destino}")
                continue

            with sftp.abrir_arquivo(origem_remota, "rb") as arquivo_remoto:
                conteudo_xlsx = arquivo_remoto.read()

            conteudo_csv = _converter_xlsx_para_csv(conteudo_xlsx)
            _salvar_csv_no_destino(destino_arquivo, conteudo_csv)
            arquivos_processados.append(
                criar_item_transferencia(
                    arquivo=arquivo["nome"],
                    origem=origem_remota,
                    destino=destino_arquivo,
                    observacao="XLSX convertido para CSV.",
                )
            )
            print(f"[OK] Arquivo convertido e salvo em: {destino_arquivo}")
    finally:
        sftp.fechar()

    return arquivos_processados


def executar_zeta_mis() -> list[str]:
    """Executa o fluxo ZETA para Carrinho Abandonado e Acionamentos."""
    credencial = _obter_credencial(71)
    origem_base = obter_variavel("DIRETORIO_SFTP_ORIGEM_ZETA").strip()
    destino_base = resolver_destino_execucao(
        obter_variavel("DIRETORIO_72_ZETA").strip(),
        "zeta_mis",
    )

    sftp = SFTPClient(credencial.hostname, credencial.usuario, credencial.porta, password=credencial.senha)
    _criar_smb(obter_config_servidor_72())

    try:
        arquivos_processados = []
        arquivos_processados.extend(
            _executar_zeta_mis_tipo(
                sftp=sftp,
                origem=_montar_caminho_sftp(origem_base, "Carrinho_Abandonado"),
                destino=_montar_caminho_smb(destino_base, "CARRINHO_ABANDONADO"),
                descricao="Carrinho Abandonado",
            )
        )
        arquivos_processados.extend(
            _executar_zeta_mis_tipo(
                sftp=sftp,
                origem=_montar_caminho_sftp(origem_base, "Ocorrencias_dia_anterior"),
                destino=_montar_caminho_smb(destino_base, "ACIONAMENTOS"),
                descricao="Acionamentos",
            )
        )
        return arquivos_processados
    finally:
        sftp.fechar()


def executar_delta(servidor_destino: str) -> list[str]:
    """Executa o fluxo Delta deduplicando por assinatura no banco."""
    arquivos_processados = []
    credencial = _obter_credencial(65)
    origem_busca = obter_variavel("DIRETORIO_SFTP_DELTA").strip()
    destino_env = "DIRETORIO_72_DESTINO_DELTA" if servidor_destino == "72" else "DIRETORIO_71_DESTINO_DELTA"
    destino_busca = resolver_destino_execucao(
        obter_variavel(destino_env).strip(),
        f"delta_{servidor_destino}",
    )
    config_smb = obter_config_servidor_72() if servidor_destino == "72" else obter_config_servidor_71()

    robo_nome = "delta" if servidor_destino == "72" else "delta_71"
    repositorio_processados = ArquivosProcessadosRepository()
    repositorio_processados.garantir_tabela()

    sftp = SFTPClient(credencial.hostname, credencial.usuario, credencial.porta, password=credencial.senha)
    _criar_smb(config_smb)

    try:
        arquivos = sorted(sftp.listar_arquivos(origem_busca, ".csv"))
        if not arquivos:
            print("Nenhum arquivo csv encontrado no diretorio remoto.")
            return []

        assinaturas_do_dia = repositorio_processados.listar_assinaturas_do_dia(robo_nome)
        hoje = date.today()

        for arquivo in arquivos:
            nome_original = os.path.basename(arquivo.replace("\\", "/"))
            origem_remota = f"{origem_busca}/{nome_original}"
            info = sftp.stat(origem_remota)
            assinatura = _gerar_assinatura_remota(nome_original, info.st_size, info.st_mtime)
            mtime_remoto = int(info.st_mtime)
            data_hora = datetime.fromtimestamp(mtime_remoto)
            nome_destino = nome_original

            if not _nome_arquivo_contem_data(nome_original):
                nome_destino = _gerar_nome_com_timestamp(nome_original, data_hora)

            # So processa arquivos modificados HOJE. Arquivos de dias anteriores
            # que continuam no SFTP sao ignorados de proposito.
            if data_hora.date() != hoje:
                print(f"Arquivo nao e do dia, ignorado: {nome_original}")
                continue

            # Deduplica dentro do dia pela assinatura (nome|tamanho|mtime).
            # Mesma assinatura ja processada hoje -> ignora. Se o arquivo foi
            # modificado ao longo do dia (tamanho ou mtime), a assinatura muda
            # e ele e transferido novamente.
            if assinatura in assinaturas_do_dia:
                print(f"Arquivo do dia ja processado: {nome_original}")
                continue

            destino_arquivo = os.path.join(destino_busca, nome_destino)

            _mover_sftp_para_smb_em_blocos(sftp, origem_remota, destino_arquivo)
            sha256 = _calcular_sha256(destino_arquivo)
            repositorio_processados.registrar(
                robo_nome=robo_nome,
                nome_original=nome_original,
                assinatura=assinatura,
                tamanho=int(info.st_size),
                mtime_remoto=mtime_remoto,
                nome_destino=nome_destino,
                sha256=sha256,
                hostname=socket.gethostname(),
                pid=os.getpid(),
            )
            assinaturas_do_dia.add(assinatura)
            arquivos_processados.append(criar_item_transferencia(nome_original, origem_remota, destino_arquivo))
            print(f"[OK] Finalizado: {nome_original}")
    finally:
        sftp.fechar()

    return arquivos_processados


def _executar_zeta_mis_tipo(sftp: SFTPClient, origem: str, destino: str, descricao: str) -> list[dict]:
    """Processa uma pasta ZETA, extrai TXT dos ZIPs e salva no destino."""
    arquivos_processados = []
    smbclient.makedirs(destino, exist_ok=True)
    destino_importado = _montar_caminho_smb(destino, "Importado")
    arquivos_existentes = _listar_nomes_txt_smb([destino, destino_importado])
    arquivos_existentes.update(_listar_nomes_txt_banco_logs("zeta_mis"))
    arquivos = _listar_zips_zeta_do_dia(sftp, origem)

    if not arquivos:
        print(f"Nenhum ZIP ZETA encontrado para {descricao}.")
        return arquivos_processados

    for arquivo_zip in arquivos:
        origem_zip = _montar_caminho_sftp(origem, arquivo_zip)
        arquivos_extraidos = _extrair_txt_zip_sftp_para_smb(
            sftp=sftp,
            origem_zip=origem_zip,
            destino=destino,
            arquivos_existentes=arquivos_existentes,
        )

        for destino_txt in arquivos_extraidos:
            arquivos_existentes.add(os.path.basename(destino_txt).lower())
            arquivos_processados.append(
                criar_item_transferencia(
                    arquivo=os.path.basename(destino_txt),
                    origem=origem_zip,
                    destino=destino_txt,
                    observacao=f"TXT extraido do ZIP ZETA: {arquivo_zip}",
                )
            )

    return arquivos_processados


def _listar_zips_zeta_do_dia(sftp: SFTPClient, origem: str) -> list[str]:
    """Lista ZIPs que possuem a data de referencia no nome."""
    datas_validas = _datas_validas_zeta()
    arquivos = sftp.listar_arquivos(origem, ".zip")
    return sorted(
        arquivo
        for arquivo in arquivos
        if any(data in arquivo for data in datas_validas)
    )


def _datas_validas_zeta() -> list[str]:
    """Retorna datas aceitas no nome do arquivo ZETA.

    O fluxo aceita hoje e ontem porque a pasta de ocorrencias representa
    dados do dia anterior e pode ser processada na manha seguinte.
    """
    hoje = date.today()
    return [
        hoje.strftime("%Y%m%d"),
        (hoje - timedelta(days=1)).strftime("%Y%m%d"),
    ]


def _listar_nomes_txt_smb(pastas: list[str]) -> set[str]:
    """Lista nomes de TXT ja existentes no SMB para evitar duplicidade exata."""
    existentes = set()
    for pasta in pastas:
        try:
            for item in smbclient.scandir(pasta):
                if item.is_file() and item.name.lower().endswith(".txt"):
                    existentes.add(item.name.lower())
        except FileNotFoundError:
            continue
    return existentes


def _listar_nomes_txt_banco_logs(robo_nome: str) -> set[str]:
    """Lista TXT ja registrados no banco de logs como transferidos."""
    return {
        arquivo
        for arquivo in _listar_arquivos_banco_logs(robo_nome)
        if arquivo.endswith(".txt")
    }


def _listar_arquivos_banco_logs(robo_nome: str) -> set[str]:
    """Lista arquivos ja registrados no banco de logs como transferidos."""
    try:
        return RobotLogsRepository().listar_arquivos_transferidos(robo_nome)
    except Exception as erro:
        print(f"[AVISO_LOG] Nao foi possivel consultar arquivos ja logados: {erro}")
        return set()


def _extrair_txt_zip_sftp_para_smb(
    sftp: SFTPClient,
    origem_zip: str,
    destino: str,
    arquivos_existentes: set[str],
) -> list[str]:
    """Abre o ZIP no SFTP e grava apenas TXT que ainda nao existem no SMB."""
    arquivos_extraidos = []

    with sftp.abrir_arquivo(origem_zip, "rb") as arquivo_remoto:
        conteudo_zip = arquivo_remoto.read()

    with zipfile.ZipFile(io.BytesIO(conteudo_zip)) as zip_ref:
        for nome_interno in zip_ref.namelist():
            if nome_interno.endswith("/") or not nome_interno.lower().endswith(".txt"):
                continue

            nome_txt = os.path.basename(nome_interno.replace("\\", "/"))
            if nome_txt.lower() in arquivos_existentes:
                print(f"TXT ja existe no destino: {nome_txt}")
                continue

            destino_txt = _montar_caminho_smb(destino, nome_txt)
            with smbclient.open_file(destino_txt, mode="wb") as arquivo_destino:
                arquivo_destino.write(zip_ref.read(nome_interno))

            arquivos_extraidos.append(destino_txt)
            print(f"[OK] TXT extraido ZETA: {nome_txt}")

    return arquivos_extraidos


def _montar_caminho_sftp(base: str, *partes: str) -> str:
    """Monta caminho SFTP usando barra normal."""
    caminho = base.rstrip("/")
    for parte in partes:
        caminho += "/" + parte.strip("/")
    return caminho or "/"


def _montar_caminho_smb(base: str, *partes: str) -> str:
    """Monta caminho SMB usando barra invertida."""
    caminho = base.rstrip("\\/")
    for parte in partes:
        caminho += "\\" + parte.strip("\\/")
    return caminho


def executar_alfacarga() -> list[str]:
    """Executa o fluxo AlfaCarga SMB para SMB."""
    arquivos_processados = []
    config_origem = obter_config_servidor_64()
    config_destino = obter_config_servidor_71()
    smbclient.reset_connection_cache()
    _criar_smb(config_origem)
    _criar_smb(config_destino)

    origem_busca = obter_variavel("DIRETORIO_64_ORIGEM_WILLBANCK")
    destino = resolver_destino_execucao(
        obter_variavel("DIRETORIO_71_DESTINO_BANCOALFA"),
        "alfacarga",
    )
    destino2 = resolver_destino_execucao(
        obter_variavel("DIRETORIO_71_DESTINO_BANCOALFA2"),
        "alfacarga_ok",
    )
    data_hoje = datetime.now().strftime("%Y%m%d")
    padroes_texto = [f"Base_diaria_para_integracao{data_hoje}.csv"]
    padroes_regex = [re.compile(fnmatch.translate(padrao)) for padrao in padroes_texto]
    arquivos = _buscar_smb_por_fnmatch(origem_busca, padroes_texto)

    if not arquivos:
        origem_busca = origem_busca.rstrip("\\/") + "/ok"
        arquivos = _buscar_smb_por_fnmatch(origem_busca, padroes_texto)

    arquivos_logados = _listar_arquivos_banco_logs("alfacarga")
    for arquivo in arquivos:
        origem = os.path.join(origem_busca, arquivo)
        destino_arquivo = os.path.join(destino, arquivo)
        if smbclient.path.exists(destino_arquivo) or arquivo.lower() in arquivos_logados:
            print(f"Arquivo ja existe no destino: {destino_arquivo}")
            continue
        _copiar_smb_para_smb(origem, destino_arquivo)
        converter_csv_smb_para_utf8_virgula(destino_arquivo)
        arquivos_processados.append(criar_item_transferencia(arquivo, origem, destino_arquivo))

    mover_restantes_por_padrao(destino, destino2, padroes_regex)
    return arquivos_processados


def _obter_credencial(id_cedente: int):
    """Busca credencial no banco padrao."""
    repo = DatabaseCredentialsRepository(obter_config_banco_66("DB_DESENVOLVIMENTO"))
    return repo.obter_credencial(id_cedente)


def _criar_smb(config: dict) -> SMBClient:
    """Cria e conecta uma sessao SMB."""
    smb = SMBClient(config["ipServidor"], config["usuario"], config["senha"])
    smb.conectar()
    return smb


def _copiar_ftp_para_smb(ftp: FTPClient, origem: str, smb: SMBClient, destino: str) -> None:
    """Copia um arquivo FTP para SMB."""
    with ftp.abrir_arquivo(origem) as origem_file:
        conteudo = origem_file.read()
    with smb.gerar_caminho_destino(destino) as destino_file:
        destino_file.write(conteudo)


def _copiar_smb_para_smb(origem: str, destino: str) -> None:
    """Copia um arquivo entre pastas SMB com tentativas se estiver bloqueado."""
    for tentativa in range(1, MAX_TENTATIVAS_ARQUIVO_BLOQUEADO + 1):
        try:
            with smbclient.open_file(origem, mode="rb") as origem_file:
                with smbclient.open_file(destino, mode="wb") as destino_file:
                    while True:
                        chunk = origem_file.read(4 * 1024 * 1024)
                        if not chunk:
                            break
                        destino_file.write(chunk)
                    destino_file.flush()
            return
        except Exception as erro:
            if not _erro_arquivo_bloqueado(erro) or tentativa == MAX_TENTATIVAS_ARQUIVO_BLOQUEADO:
                raise
            print(
                f"[ARQUIVO_BLOQUEADO] Tentativa {tentativa}/{MAX_TENTATIVAS_ARQUIVO_BLOQUEADO}. "
                f"Aguardando {SEGUNDOS_ESPERA_ARQUIVO_BLOQUEADO}s para copiar novamente: {origem}"
            )
            sleep(SEGUNDOS_ESPERA_ARQUIVO_BLOQUEADO)


def _erro_arquivo_bloqueado(erro: Exception) -> bool:
    """Verifica se o erro indica arquivo em uso por outro processo."""
    mensagem = str(erro).lower()
    return "0xc0000043" in mensagem or "being used by another process" in mensagem


def _buscar_smb_por_fnmatch(pasta: str, padroes: list[str]) -> list[str]:
    """Busca arquivos SMB por padroes fnmatch."""
    encontrados = []
    for entry in smbclient.scandir(pasta):
        if entry.is_file() and any(fnmatch.fnmatch(entry.name, padrao) for padrao in padroes):
            encontrados.append(entry.name)
    return encontrados


def _gerar_nome_banco_iota(data_movimentacao: datetime) -> str:
    """Gera o nome final do CSV do Banco Iota."""
    return f"BOLETOS_GERADOS_ACME_{data_movimentacao.strftime('%Y%m%d')}.csv"


def _formatar_inteiro_com_mascara(valor: int, numero_formatado: str) -> str | None:
    """Formata inteiros preservando zeros a esquerda do Excel."""
    mascara = (numero_formatado or "").split(";")[0].strip()
    if re.fullmatch(r"0+", mascara):
        return f"{valor:0{len(mascara)}d}"
    return None


def _formatar_celula_excel(celula) -> str:
    """Converte uma celula Excel para texto."""
    valor = celula.value
    if valor is None:
        return ""
    if celula.is_date:
        if isinstance(valor, datetime):
            return valor.strftime("%Y-%m-%d") if valor.time() == time(0, 0) else valor.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(valor, date):
            return valor.strftime("%Y-%m-%d")
    if isinstance(valor, bool):
        return "TRUE" if valor else "FALSE"
    if isinstance(valor, int):
        return _formatar_inteiro_com_mascara(valor, celula.number_format) or str(valor)
    if isinstance(valor, float):
        if valor.is_integer():
            inteiro = int(valor)
            return _formatar_inteiro_com_mascara(inteiro, celula.number_format) or str(inteiro)
        return format(valor, "f").rstrip("0").rstrip(".")
    return str(valor)


def _converter_xlsx_para_csv(conteudo_xlsx: bytes) -> bytes:
    """Converte XLSX para CSV em memoria."""
    workbook = load_workbook(filename=io.BytesIO(conteudo_xlsx), data_only=True, read_only=True)
    try:
        worksheet = workbook.worksheets[0]
        buffer_csv = io.StringIO(newline="")
        writer = csv.writer(buffer_csv, delimiter=",", lineterminator="\n")
        for linha in worksheet.iter_rows():
            writer.writerow([_formatar_celula_excel(celula) for celula in linha])
        return buffer_csv.getvalue().encode("utf-8-sig")
    finally:
        workbook.close()


def _salvar_csv_no_destino(destino_arquivo: str, conteudo_csv: bytes) -> None:
    """Salva CSV em SMB usando arquivo temporario."""
    pasta_destino = os.path.dirname(destino_arquivo)
    arquivo_temporario = f"{destino_arquivo}.tmp"
    if not smbclient.path.exists(pasta_destino):
        smbclient.makedirs(pasta_destino, exist_ok=True)
    if smbclient.path.exists(arquivo_temporario):
        smbclient.remove(arquivo_temporario)
    with smbclient.open_file(arquivo_temporario, mode="wb") as arquivo_destino:
        arquivo_destino.write(conteudo_csv)
        arquivo_destino.flush()
    if smbclient.path.exists(destino_arquivo):
        smbclient.remove(destino_arquivo)
    smbclient.rename(arquivo_temporario, destino_arquivo)


def _banco_iota_ja_transferido(destino_busca: str, data_movimentacao: datetime) -> bool:
    """Verifica se o Banco Iota ja foi transferido."""
    nome_destino = _gerar_nome_banco_iota(data_movimentacao)
    caminhos = [
        destino_busca.rstrip("\\") + "\\" + nome_destino,
        destino_busca.rstrip("\\") + "\\IMPORTADO\\" + nome_destino,
    ]
    return any(smbclient.path.exists(caminho) for caminho in caminhos)


def _gerar_nome_com_timestamp(nome_arquivo: str, data_hora_remota: datetime) -> str:
    """Adiciona timestamp ao nome do arquivo."""
    nome_base, extensao = os.path.splitext(nome_arquivo)
    return f"{nome_base}_{data_hora_remota.strftime('%Y%m%d_%H%M%S')}{extensao}"


def _nome_arquivo_contem_data(nome_arquivo: str) -> bool:
    """Verifica se o nome ja contem uma data YYYYMMDD."""
    nome_base = os.path.splitext(os.path.basename(nome_arquivo))[0]
    return bool(re.search(r"(?<!\d)(\d{8})(?!\d)", nome_base))


def _gerar_assinatura_remota(nome_arquivo: str, tamanho_bytes: int, mtime: float) -> str:
    """Gera assinatura unica para o arquivo remoto."""
    return f"{nome_arquivo}|{tamanho_bytes}|{int(mtime)}"


def _calcular_sha256(caminho_arquivo: str) -> str:
    """Calcula SHA256 de arquivo em SMB."""
    hasher = hashlib.sha256()
    with smbclient.open_file(caminho_arquivo, mode="rb") as arquivo:
        while True:
            bloco = arquivo.read(TAMANHO_BUFFER_HASH)
            if not bloco:
                break
            hasher.update(bloco)
    return hasher.hexdigest()


def _gerar_caminho_temporario_smb(destino: str) -> str:
    """Gera um caminho temporario unico na mesma pasta do arquivo final."""
    pasta_destino = os.path.dirname(destino)
    nome_arquivo = os.path.basename(destino)
    nome_temporario = f".{nome_arquivo}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    return os.path.join(pasta_destino, nome_temporario)


def _finalizar_transferencia_smb(caminho_temporario: str, destino: str) -> None:
    """Troca o arquivo temporario pelo arquivo final depois da copia completa."""
    try:
        if smbclient.path.exists(destino):
            smbclient.remove(destino)
        smbclient.rename(caminho_temporario, destino)
    except Exception:
        try:
            if smbclient.path.exists(caminho_temporario):
                smbclient.remove(caminho_temporario)
        except Exception as erro_limpeza:
            print(f"[AVISO] Nao foi possivel remover temporario {caminho_temporario}: {erro_limpeza}")
        raise


def _mover_sftp_para_smb_em_blocos(sftp: SFTPClient, origem: str, destino: str) -> None:
    """Copia arquivo SFTP para SMB em blocos grandes usando arquivo temporario."""
    tentativa = 0
    while tentativa < MAX_TENTATIVAS_TRANSFERENCIA:
        caminho_temporario = _gerar_caminho_temporario_smb(destino)
        try:
            tamanho = sftp.stat(origem).st_size
            bytes_transferidos = 0
            with sftp.abrir_arquivo(origem, "rb") as remote_file:
                with smbclient.open_file(caminho_temporario, mode="wb") as smb_file:
                    while True:
                        data = remote_file.read(TAMANHO_BUFFER_TRANSFERENCIA)
                        if not data:
                            break
                        smb_file.write(data)
                        bytes_transferidos += len(data)
                        progresso = (bytes_transferidos / tamanho) * 100 if tamanho else 100
                        print(f"\rProgresso: {progresso:.2f}%", end="", flush=True)
                    smb_file.flush()
            _finalizar_transferencia_smb(caminho_temporario, destino)
            print("\nTransferencia concluida com sucesso!")
            return
        except SSHException as erro:
            _remover_temporario_se_existir(caminho_temporario)
            tentativa += 1
            print(f"\n[ERRO] Conexao perdida ({erro}). Tentando reconectar ({tentativa}/{MAX_TENTATIVAS_TRANSFERENCIA})...")
            sftp.reconect()
            sleep(2)
    raise ConnectionError(f"Falha ao transferir {origem}.")


def _remover_temporario_se_existir(caminho_temporario: str) -> None:
    """Remove arquivo temporario criado em uma tentativa com erro."""
    try:
        if smbclient.path.exists(caminho_temporario):
            smbclient.remove(caminho_temporario)
    except Exception as erro:
        print(f"[AVISO] Nao foi possivel remover temporario {caminho_temporario}: {erro}")


def _enviar_drive_bsc(destino_drive: str | None, origem_servidor: str) -> None:
    """Copia o arquivo BSC para o drive local configurado."""
    try:
        if not destino_drive:
            print("Drive nao encontrado.")
            return
        if not os.path.exists(destino_drive):
            os.makedirs(destino_drive)
        destino_final = os.path.join(destino_drive, os.path.basename(origem_servidor))
        with smbclient.open_file(origem_servidor, mode="rb") as src:
            with open(destino_final, "wb") as dst:
                shutil.copyfileobj(src, dst)
    except Exception as erro:
        print(f"Erro ao enviar arquivo para o Drive: {erro}")


def _enviar_email_bsc(arquivo: str, data_email: str, remetente: str, senha: str) -> None:
    """Envia e-mail do BSC Mu."""
    if not remetente or not senha:
        print("E-mail nao enviado")
        return

    to = ["colaborador12@empresa.example"]
    cc = [
        "desenvolvimento@empresa.example",
        "mis@empresa.example",
        "colaborador14@empresa.example",
        "colaborador15@empresa.example",
        "planejamento@empresa.example",
    ]

    msg = EmailMessage()
    msg["Subject"] = f"BSC Mu | {data_email}"
    msg["From"] = remetente
    msg["To"] = ", ".join(to)
    msg["Cc"] = ", ".join(cc)
    msg.set_content(f"Arquivo {arquivo} disponibilizado na pasta BSC MU.")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(remetente, senha)
            smtp.send_message(msg)
    except Exception as erro:
        print(f"Erro ao enviar e-mail: {erro}")
