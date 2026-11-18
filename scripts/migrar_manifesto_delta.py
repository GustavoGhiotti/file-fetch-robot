"""Migracao unica: semeia a tabela de assinaturas com os processados de HOJE.

Como o Delta agora so olha arquivos do dia, o unico risco no momento do
deploy e retransferir os arquivos que ja foram processados HOJE pelo robo antigo
(a tabela nova comeca vazia). Este script importa apenas os registros de hoje do
manifesto em disco (.delta_processados.jsonl) para a tabela
ROBO_ARQUIVO_PROCESSADO, evitando esse reenvio no cutover.

Rodar UMA vez, no dia do deploy, antes de liberar o agendador novo.
"""

from datetime import date, datetime
import json

import smbclient

from src.infrastructure.config.env import obter_variavel
from src.infrastructure.config.settings import (
    obter_config_servidor_71,
    obter_config_servidor_72,
)
from src.infrastructure.repositories.arquivos_processados_repository import (
    ArquivosProcessadosRepository,
)
from src.infrastructure.smb.smb_client import SMBClient


NOME_ARQUIVO_CONTROLE_DELTA = ".delta_processados.jsonl"


def _criar_smb(config: dict) -> None:
    """Conecta uma sessao SMB para o servidor informado."""
    smb = SMBClient(config["ipServidor"], config["usuario"], config["senha"])
    smb.conectar()


def _extrair_tamanho_da_assinatura(assinatura: str) -> int | None:
    """Extrai o tamanho (nome|tamanho|mtime) da assinatura remota."""
    partes = assinatura.rsplit("|", 2)
    if len(partes) == 3 and partes[1].isdigit():
        return int(partes[1])
    return None


def migrar(robo_nome: str, destino_env: str, config_smb: dict) -> None:
    """Importa as assinaturas processadas hoje de um manifesto para o banco."""
    destino = obter_variavel(destino_env).strip()
    caminho_manifesto = destino.rstrip("\\/") + "\\" + NOME_ARQUIVO_CONTROLE_DELTA

    _criar_smb(config_smb)
    repositorio = ArquivosProcessadosRepository()
    repositorio.garantir_tabela()
    ja_existentes = repositorio.listar_assinaturas(robo_nome)

    total_importados = 0
    total_ignorados = 0
    vistos = set()

    try:
        with smbclient.open_file(caminho_manifesto, mode="r", encoding="utf-8") as arquivo:
            for linha in arquivo:
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    registro = json.loads(linha)
                except json.JSONDecodeError:
                    continue

                assinatura = registro.get("assinatura_remota")
                if not assinatura:
                    continue

                # So importa o que foi processado hoje.
                processado_em = registro.get("processado_em")
                if not processado_em:
                    continue
                try:
                    if datetime.fromisoformat(processado_em).date() != date.today():
                        continue
                except ValueError:
                    continue

                if assinatura in ja_existentes or assinatura in vistos:
                    total_ignorados += 1
                    continue

                repositorio.registrar(
                    robo_nome=robo_nome,
                    nome_original=registro.get("nome_original") or assinatura.split("|")[0],
                    assinatura=assinatura,
                    tamanho=_extrair_tamanho_da_assinatura(assinatura),
                    mtime_remoto=registro.get("mtime_remoto"),
                    nome_destino=registro.get("nome_gerado"),
                    sha256=registro.get("sha256"),
                )
                vistos.add(assinatura)
                total_importados += 1
    except FileNotFoundError:
        print(f"[{robo_nome}] Manifesto nao encontrado em {caminho_manifesto}. Nada a migrar.")
        return

    print(
        f"[{robo_nome}] Importadas {total_importados} assinaturas "
        f"({total_ignorados} ja existiam) de {caminho_manifesto}."
    )


if __name__ == "__main__":
    migrar("delta", "DIRETORIO_72_DESTINO_DELTA", obter_config_servidor_72())
    migrar("delta_71", "DIRETORIO_71_DESTINO_DELTA", obter_config_servidor_71())
    print("Migracao concluida.")
