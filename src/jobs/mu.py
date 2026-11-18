"""Configuracao dos jobs do Mu."""

import re
from datetime import date, timedelta

from src.domain.models.job_config import JobConfig
from src.infrastructure.config.env import obter_variavel


def criar_job_mu() -> JobConfig:
    """Cria a configuracao do job principal do Mu.

    Retorna:
        Configuracao usada para buscar arquivos do Mu.
    """
    return JobConfig(
        nome="mu",
        id_cedente=3,
        origem="",  # Hoje vem do banco pelo campo ORIGEM_CARGA.
        destino=r"\\10.0.0.64\arquivos\carga\Mu Cyber\PagamentosPix",
        extensao=".txt",
        padroes_nome=[],
        servidor_destino="64",
        tipo_origem="ftp",
        usar_origem_banco=True,
        nomes_obrigatorios=["RAJADAS_PAGTOS_PIX"],
        mover_ftp_para="PIX",
    )


def criar_job_mu_retirada() -> JobConfig:
    """Cria a configuracao do job de retirada do Mu."""
    return JobConfig(
        nome="mu_retirada",
        id_cedente=3,
        origem="",
        destino=obter_variavel("DIRETORIO_71_MU_RETIRADA"),
        extensao=".txt",
        padroes_nome=[],
        servidor_destino="71",
        tipo_origem="ftp",
        usar_origem_banco=True,
    )


def criar_job_mu_bat() -> JobConfig:
    """Cria a configuracao do job de batimento do Mu."""
    mes = date.today() - timedelta(days=1)
    mes_referencia = mes.strftime("%Y%m")
    ano_referencia = mes_referencia[:4]
    mes_numero = mes_referencia[4:6]

    return JobConfig(
        nome="mu_bat",
        id_cedente=3,
        origem=obter_variavel("ORIGEM_MU"),
        destino=obter_variavel("DESTINO_MU"),
        extensao=".txt",
        padroes_nome=[
            re.compile(fr"^BAT_ACORDO_PGTO_CHI_(?:{mes_referencia}\d{{2}}|\d{{2}}{mes_numero}{ano_referencia}).*\.txt$"),
            re.compile(fr"^BAT_ACORDO_CHI_(?:{mes_referencia}\d{{2}}|\d{{2}}{mes_numero}{ano_referencia}).*\.txt$"),
            re.compile(fr"^BAT_CONTRATOS_CHI_(?:{mes_referencia}\d{{2}}|\d{{2}}{mes_numero}{ano_referencia}).*\.txt$"),
        ],
        servidor_destino="64",
        tipo_origem="ftp",
        origens_alternativas=[
            obter_variavel("ORIGEM_MU", obrigatoria=False),
            obter_variavel("ORIGEM_MU2", obrigatoria=False),
        ],
        destino_ok=obter_variavel("DESTINO_MU", obrigatoria=False) + r"\ok",
        processamento_especial="envia Telegram e usa filtro mensal no FTP",
    )


def criar_job_mu_bsc() -> JobConfig:
    """Cria a configuracao do job BSC do Mu."""
    return JobConfig(
        nome="mu_bsc",
        id_cedente=3,
        origem="",
        destino="",
        extensao=".txt",
        padroes_nome=[],
        servidor_destino="64",
        tipo_origem="ftp",
        processamento_especial="envia email/telegram e possui copia local",
    )
