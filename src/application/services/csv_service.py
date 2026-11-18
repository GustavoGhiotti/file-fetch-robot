"""Funcoes para trabalhar com arquivos CSV."""

import csv
import io

import pandas as pd
import smbclient


def detectar_delimitador_robusto(sample: str) -> str:
    """Descobre qual separador o arquivo CSV esta usando.

    Recebe:
        sample: um pedaco do conteudo do arquivo em texto.

    Retorna:
        Separador encontrado. Se nao conseguir descobrir, retorna ";".
    """
    candidatos = [";", ",", "|", "\t"]
    linhas = [linha for linha in sample.splitlines() if linha.strip()][:200]

    melhor = None
    melhor_score = (-1, -1, -1.0)

    for delimitador in candidatos:
        colunas_por_linha = []

        for linha in linhas:
            try:
                row = next(csv.reader([linha], delimiter=delimitador, quotechar='"'))
                colunas_por_linha.append(len(row))
            except Exception:
                continue

        if not colunas_por_linha:
            continue

        moda_colunas = max(set(colunas_por_linha), key=colunas_por_linha.count)
        qtd_linhas_moda = colunas_por_linha.count(moda_colunas)
        consistencia = qtd_linhas_moda / len(colunas_por_linha)
        score = (moda_colunas, qtd_linhas_moda, consistencia)

        if moda_colunas > 1 and score > melhor_score:
            melhor_score = score
            melhor = delimitador

    return melhor if melhor else ";"


def validar_csv_virgula(conteudo: bytes) -> bool:
    """Verifica se o CSV esta separado por virgula.

    Recebe:
        conteudo: conteudo do arquivo em bytes.

    Retorna:
        True se o arquivo parece estar separado por virgula.
        False se nao parece estar separado por virgula.
    """
    texto = conteudo.decode("utf-8-sig", errors="ignore")
    linhas = [linha for linha in texto.splitlines() if linha.strip()][:200]

    if not linhas:
        return False

    colunas_por_linha = []

    for linha in linhas:
        try:
            row = next(csv.reader([linha], delimiter=",", quotechar='"'))
            colunas_por_linha.append(len(row))
        except Exception:
            continue

    if not colunas_por_linha:
        return False

    moda_colunas = max(set(colunas_por_linha), key=colunas_por_linha.count)
    consistencia = colunas_por_linha.count(moda_colunas) / len(colunas_por_linha)

    return moda_colunas >= 2 and consistencia >= 0.8


def converter_csv_smb_para_utf8_virgula(caminho_arquivo: str) -> bool:
    """Converte um CSV no SMB para UTF-8 com virgula.

    Recebe:
        caminho_arquivo: caminho completo do arquivo CSV no SMB.

    Retorna:
        True se converteu e validou o arquivo.
        False se houve erro ou se o CSV final ficou invalido.
    """
    nome_base = caminho_arquivo.rsplit("\\", 1)[-1]
    print(f"[CONVERTENDO] {nome_base}...")

    try:
        with smbclient.open_file(caminho_arquivo, mode="rb") as arquivo:
            conteudo = arquivo.read()

        sample = conteudo.decode("latin-1", errors="ignore")[:20000]
        delimitador_origem = detectar_delimitador_robusto(sample)
        encodings_teste = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
        ultimo_erro = None
        dataframe = None

        for encoding in encodings_teste:
            try:
                dataframe = pd.read_csv(
                    io.BytesIO(conteudo),
                    sep=delimitador_origem,
                    engine="python",
                    encoding=encoding,
                    dtype=str,
                    keep_default_na=False,
                    on_bad_lines="error",
                )
                break
            except (UnicodeDecodeError, pd.errors.ParserError) as erro:
                ultimo_erro = erro

        if dataframe is None:
            raise ultimo_erro or ValueError("Nao foi possivel ler o CSV.")

        csv_utf8 = dataframe.to_csv(index=False, sep=",", encoding="utf-8-sig")

        with smbclient.open_file(caminho_arquivo, mode="wb") as arquivo_saida:
            arquivo_saida.write(csv_utf8.encode("utf-8-sig"))

        with smbclient.open_file(caminho_arquivo, mode="rb") as arquivo_validacao:
            conteudo_validacao = arquivo_validacao.read()

        if not validar_csv_virgula(conteudo_validacao):
            smbclient.remove(caminho_arquivo)
            print(f"[REMOVIDO] CSV final sem estrutura valida: {nome_base}")
            return False

        print(f"[OK] Convertido para UTF-8 e validado: {nome_base}")
        return True

    except Exception as erro:
        print(f"[ERRO] Falha ao converter {nome_base}: {erro}")
        try:
            if smbclient.path.exists(caminho_arquivo):
                smbclient.remove(caminho_arquivo)
                print(f"[REMOVIDO] Arquivo com falha: {nome_base}")
        except Exception as erro_remove:
            print(f"[ERRO] Falha ao remover {nome_base}: {erro_remove}")
        return False


def regravar_como_excel_smb(caminho_arquivo: str) -> bool:
    """Regrava o CSV como ANSI, separado por ponto e virgula e com CRLF.

    Recebe:
        caminho_arquivo: caminho completo do arquivo no SMB.

    Retorna:
        True se conseguiu regravar.
        False se houve erro.
    """
    try:
        with smbclient.open_file(caminho_arquivo, mode="rb") as arquivo:
            raw = arquivo.read()

        encoding = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "cp1252"
        texto = raw.decode(encoding, errors="replace")
        texto = texto.replace("\r\n", "\n").replace("\r", "\n")

        sample = "\n".join(texto.splitlines()[:100])
        if "," in sample and ";" not in sample:
            delimitador_original = ","
        elif "\t" in sample:
            delimitador_original = "\t"
        else:
            delimitador_original = ";"

        reader = csv.reader(io.StringIO(texto), delimiter=delimitador_original)
        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter=";", lineterminator="\r\n")

        for row in reader:
            writer.writerow(row)

        temp_path = caminho_arquivo + ".tmp"
        with smbclient.open_file(temp_path, mode="wb") as arquivo_temp:
            arquivo_temp.write(output.getvalue().encode("cp1252", errors="replace"))
            arquivo_temp.flush()

        if smbclient.path.exists(caminho_arquivo):
            smbclient.remove(caminho_arquivo)
        smbclient.rename(temp_path, caminho_arquivo)
        print(f"Arquivo regravado com sucesso: {caminho_arquivo}")
        return True

    except Exception as erro:
        print(f"Falha ao regravar arquivo no formato Excel: {erro}")
        return False
