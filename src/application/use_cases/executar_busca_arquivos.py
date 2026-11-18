"""Fluxo principal para buscar arquivos e enviar para o destino."""

from datetime import date, datetime

from src.application.services.csv_service import (
    converter_csv_smb_para_utf8_virgula,
    regravar_como_excel_smb,
)
from src.application.services.transfer_service import (
    arquivo_ja_processado,
    caminho_existe_smb,
    copiar_remoto_para_smb,
    montar_caminho_remoto,
    montar_caminho_smb,
    mover_restantes_por_padrao,
)
from src.application.services.zip_service import extrair_zip_smb, remover_arquivo_smb
from src.infrastructure.repositories.robot_logs_repository import RobotLogsRepository
from src.shared.transfer_log import criar_item_transferencia


class ExecutarBuscaArquivo:
    """Executa o fluxo padrao de busca de arquivos."""

    def __init__(self, cliente_remoto, servidor_destino, config):
        """Guarda as dependencias necessarias para executar o job."""
        self.cliente_remoto = cliente_remoto
        self.servidor_destino = servidor_destino
        self.config = config

    def executar(self) -> list[str]:
        """Busca arquivos na origem, copia para o destino e trata se necessario.

        Retorna:
            Lista com os caminhos dos arquivos gerados no destino.
        """
        if self.config.processamento_especial:
            raise NotImplementedError(
                f"Job {self.config.nome} precisa de migracao especial: "
                f"{self.config.processamento_especial}"
            )

        arquivos_gerados = []
        arquivos = self._listar_arquivos()

        if not arquivos:
            print(f"Nenhum arquivo encontrado para o job {self.config.nome}.")
            return arquivos_gerados

        arquivos_logados = self._listar_arquivos_logados()
        arquivos_existentes = self._listar_destino_com_ok()
        arquivos_existentes.extend(arquivos_logados)

        for arquivo in arquivos:
            if self._deve_ignorar_por_nome(arquivo):
                continue

            destino = montar_caminho_smb(self.config.destino, arquivo)

            if self.config.verificar_existencia_exata and (
                caminho_existe_smb(destino) or arquivo.lower() in arquivos_logados
            ):
                print(f"Arquivo ja existe: {destino}")
                continue

            if self.config.verificar_por_prefixo and arquivo_ja_processado(arquivo, arquivos_existentes):
                print(f"Arquivo ja processado: {arquivo}")
                continue

            origem = montar_caminho_remoto(self.config.origem, arquivo)
            copiar_remoto_para_smb(self.cliente_remoto, origem, destino)
            arquivos_gerados.append(
                criar_item_transferencia(
                    arquivo=arquivo,
                    origem=origem,
                    destino=destino,
                )
            )

            arquivos_tratados = self._tratar_arquivo_destino(destino)
            arquivos_gerados.extend(arquivos_tratados)

            self._mover_origem_ftp_se_precisar(origem, arquivo)

        self._mover_restantes_se_precisar()
        return arquivos_gerados

    def _listar_arquivos(self) -> list[str]:
        """Lista arquivos de acordo com a configuracao do job."""
        if self.config.selecionar_mais_recente_do_dia:
            return self._listar_arquivo_mais_recente_do_dia()

        origens = self.config.origens_alternativas or [self.config.origem]
        arquivos = []

        for origem in origens:
            if not origem:
                continue
            encontrados = self.cliente_remoto.listar_arquivos(
                origem,
                self.config.extensao,
                self.config.padroes_nome,
            )
            arquivos.extend(encontrados)

        return list(dict.fromkeys(arquivos))

    def _listar_arquivo_mais_recente_do_dia(self) -> list[str]:
        """Seleciona o arquivo mais recente modificado hoje."""
        arquivos = self.cliente_remoto.listar_arquivos(
            self.config.origem,
            self.config.extensao,
            self.config.padroes_nome,
        )
        arquivos_info = []

        for arquivo in arquivos:
            caminho = montar_caminho_remoto(self.config.origem, arquivo)
            info = self.cliente_remoto.stat(caminho)
            modificado_em = datetime.fromtimestamp(info.st_mtime)
            if modificado_em.date() == date.today():
                arquivos_info.append((arquivo, modificado_em))

        arquivos_info.sort(key=lambda item: item[1], reverse=True)
        return [arquivos_info[0][0]] if arquivos_info else []

    def _listar_destino_com_ok(self) -> list[str]:
        """Lista arquivos no destino principal e na pasta ok, se existir."""
        arquivos = self.servidor_destino.listar_arquivos(self.config.destino)

        if self.config.destino_ok:
            try:
                arquivos.extend(self.servidor_destino.listar_arquivos(self.config.destino_ok))
            except Exception:
                pass

        return arquivos

    def _listar_arquivos_logados(self) -> list[str]:
        """Lista arquivos ja registrados no banco como transferidos."""
        try:
            return list(RobotLogsRepository().listar_arquivos_transferidos(self.config.nome))
        except Exception as erro:
            print(f"[AVISO_LOG] Nao foi possivel consultar arquivos ja logados: {erro}")
            return []

    def _deve_ignorar_por_nome(self, arquivo: str) -> bool:
        """Verifica filtros simples de texto no nome do arquivo."""
        if not self.config.nomes_obrigatorios:
            return False
        return not any(texto in arquivo for texto in self.config.nomes_obrigatorios)

    def _tratar_arquivo_destino(self, destino: str) -> list[str]:
        """Executa tratamentos depois da copia."""
        arquivos_tratados = []

        if self.config.regravar_como_excel:
            regravar_como_excel_smb(destino)

        if self.config.extrair_zip and destino.lower().endswith(".zip"):
            extraidos = extrair_zip_smb(destino, self.config.destino)
            for extraido in extraidos:
                arquivos_tratados.append(
                    criar_item_transferencia(
                        arquivo=extraido.rsplit("\\", 1)[-1],
                        origem=destino,
                        destino=extraido,
                        observacao="Arquivo extraido do ZIP.",
                    )
                )

            if self.config.remover_zip:
                remover_arquivo_smb(destino)

            for extraido in extraidos:
                if self.config.converter_csv and extraido.lower().endswith(".csv"):
                    converter_csv_smb_para_utf8_virgula(extraido)

        elif self.config.converter_csv and destino.lower().endswith(".csv"):
            converter_csv_smb_para_utf8_virgula(destino)

        return arquivos_tratados

    def _mover_origem_ftp_se_precisar(self, origem: str, arquivo: str) -> None:
        """Move arquivo no FTP quando o job pedir."""
        if self.config.tipo_origem != "ftp" or not self.config.mover_ftp_para:
            return
        destino_ftp = montar_caminho_remoto(self.config.mover_ftp_para, arquivo)
        self.cliente_remoto.mover_arquivo(origem, destino_ftp)

    def _mover_restantes_se_precisar(self) -> None:
        """Move arquivos fora do padrao para a pasta ok."""
        if not self.config.mover_restantes_para_ok or not self.config.destino_ok:
            return
        mover_restantes_por_padrao(
            self.config.destino,
            self.config.destino_ok,
            self.config.padroes_nome,
        )
