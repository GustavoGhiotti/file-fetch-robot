"""Funcoes para montar detalhes de arquivos transferidos."""

from datetime import datetime
import os


def criar_item_transferencia(
    arquivo: str,
    origem: str,
    destino: str,
    transferido_em: datetime | None = None,
    observacao: str | None = None,
) -> dict:
    """Monta um item padrao para salvar no JSON de logs.

    Recebe:
        arquivo: nome do arquivo transferido.
        origem: caminho usado como origem.
        destino: caminho usado como destino.
        transferido_em: horario da transferencia.
        observacao: detalhe adicional, quando existir.

    Retorna:
        Dicionario pronto para ser salvo em DETALHES_JSON.
    """
    horario = transferido_em or datetime.now()

    item = {
        "arquivo": arquivo,
        "origem": origem,
        "destino": destino,
        "transferido_em": horario.isoformat(timespec="seconds"),
    }

    if observacao:
        item["observacao"] = observacao

    return item


def nome_arquivo_do_caminho(caminho: str) -> str:
    """Extrai o nome do arquivo de um caminho SMB, FTP ou SFTP."""
    normalizado = caminho.replace("\\", "/")
    return os.path.basename(normalizado)
