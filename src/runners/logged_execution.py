"""Wrapper para executar robos salvando logs relevantes no banco."""

from collections.abc import Callable
from datetime import datetime
import getpass
import json
import os
import socket
import traceback
from uuid import uuid4

from src.domain.models.robo_log import RoboLog
from src.infrastructure.repositories.robot_logs_repository import RobotLogsRepository


def executar_com_log(robo_nome: str, script_nome: str, funcao: Callable[[], object]) -> object:
    """Executa uma funcao salvando somente sucesso com acao ou erro.

    Este wrapper evita registrar execucoes sem acao. Isso e importante para
    robos agendados a cada poucos minutos, onde muitas execucoes apenas
    confirmam que nao ha arquivo novo ou que o arquivo ja foi processado.

    Recebe:
        robo_nome: nome amigavel do robo.
        script_nome: nome do script executado.
        funcao: funcao que executa o robo.

    Retorna:
        O retorno da funcao executada.
    """
    id_execucao = uuid4()
    data_inicio = datetime.now()
    contexto = _criar_contexto_maquina()
    repositorio = RobotLogsRepository()

    try:
        resultado = funcao()
        data_fim = datetime.now()
        duracao = (data_fim - data_inicio).total_seconds()

        if _teve_acao(resultado):
            detalhes = _montar_detalhes_sucesso(resultado)

            _salvar_log_sem_quebrar(
                repositorio,
                RoboLog(
                    id_execucao=id_execucao,
                    robo_nome=robo_nome,
                    script_nome=script_nome,
                    evento_tipo="TRANSFERENCIA",
                    status="SUCESSO",
                    mensagem="Execucao realizou transferencia ou processamento.",
                    arquivos=_juntar_campo_arquivos(resultado, "arquivo"),
                    caminhos_origem=_juntar_campo_arquivos(resultado, "origem", somente_pasta=True),
                    caminhos_destino=_juntar_campo_arquivos(resultado, "destino", somente_pasta=True),
                    detalhes_json=json.dumps(detalhes, ensure_ascii=False, default=str),
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    duracao_segundos=duracao,
                    **contexto,
                ),
            )

        return resultado

    except Exception as erro:
        data_fim = datetime.now()
        duracao = (data_fim - data_inicio).total_seconds()
        detalhes = {
            "erro_tipo": type(erro).__name__,
            "erro": str(erro),
            "traceback": traceback.format_exc(),
        }

        _salvar_log_sem_quebrar(
            repositorio,
            RoboLog(
                id_execucao=id_execucao,
                robo_nome=robo_nome,
                script_nome=script_nome,
                evento_tipo="ERRO",
                status="ERRO",
                mensagem=str(erro),
                detalhes_json=json.dumps(detalhes, ensure_ascii=False),
                data_inicio=data_inicio,
                data_fim=data_fim,
                duracao_segundos=duracao,
                **contexto,
            ),
        )

        raise


def _criar_contexto_maquina() -> dict:
    """Monta dados da maquina que esta executando o robo."""
    return {
        "hostname": socket.gethostname(),
        "usuario_windows": getpass.getuser(),
        "pid": os.getpid(),
    }


def _teve_acao(resultado: object) -> bool:
    """Verifica se a execucao fez algo que merece log."""
    if resultado is None:
        return False

    if isinstance(resultado, bool):
        return resultado

    if isinstance(resultado, int | float):
        return resultado > 0

    if isinstance(resultado, str):
        return bool(resultado.strip())

    if isinstance(resultado, dict):
        if "arquivos" in resultado:
            return bool(resultado["arquivos"])
        if "total" in resultado:
            return resultado["total"] > 0
        return bool(resultado)

    if isinstance(resultado, list | tuple | set):
        return len(resultado) > 0

    return True


def _contar_itens(resultado: object) -> int:
    """Conta itens processados para salvar no JSON de detalhes."""
    if resultado is None:
        return 0
    if isinstance(resultado, bool):
        return int(resultado)
    if isinstance(resultado, int | float):
        return int(resultado)
    if isinstance(resultado, dict):
        if "arquivos" in resultado and hasattr(resultado["arquivos"], "__len__"):
            return len(resultado["arquivos"])
        if "total" in resultado:
            return int(resultado["total"])
        return len(resultado)
    if isinstance(resultado, list | tuple | set):
        return len(resultado)
    return 1


def _montar_detalhes_sucesso(resultado: object) -> dict:
    """Monta o JSON de sucesso salvo no banco."""
    if isinstance(resultado, list | tuple | set):
        return {
            "arquivos": list(resultado),
            "total_itens": len(resultado),
        }

    if isinstance(resultado, dict):
        detalhes = dict(resultado)
        detalhes.setdefault("total_itens", _contar_itens(resultado))
        return detalhes

    return {
        "resultado": resultado,
        "total_itens": _contar_itens(resultado),
    }


def _juntar_campo_arquivos(
    resultado: object,
    campo: str,
    somente_pasta: bool = False,
) -> str | None:
    """Junta campos dos arquivos processados separados por ponto e virgula."""
    if not isinstance(resultado, list | tuple | set):
        return None

    valores = []
    for item in resultado:
        if not isinstance(item, dict):
            continue

        valor = item.get(campo)
        if not valor:
            continue

        if somente_pasta:
            valor = _obter_pasta(str(valor))

        if valor not in valores:
            valores.append(valor)

    return "; ".join(valores) if valores else None


def _obter_pasta(caminho: str) -> str:
    """Retorna somente a pasta de um caminho, sem o nome do arquivo."""
    separador = "\\" if "\\" in caminho else "/"
    if separador not in caminho:
        return caminho
    return caminho.rsplit(separador, 1)[0]


def _salvar_log_sem_quebrar(repositorio: RobotLogsRepository, log: RoboLog) -> None:
    """Tenta salvar o log sem interromper o robo se o banco falhar."""
    try:
        repositorio.salvar(log)
    except Exception as erro:
        print(f"[AVISO_LOG] Nao foi possivel salvar log no banco: {erro}")
