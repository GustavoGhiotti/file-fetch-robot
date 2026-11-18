# File Fetch Robot

> **Versão de portfólio.** Código real de produção, anonimizado: nomes de empresa, clientes, pessoas, hosts, e-mails e credenciais foram trocados por valores fictícios (`Acme`, `Banco Alfa`, `10.0.0.x`, `empresa.example`). Toda configuração sensível vem do `.env` (modelo em `.env.example`). O código não aponta para nenhum sistema real.

Robô que busca arquivos de retorno/remessa nos SFTPs dos credores e os entrega no servidor interno, a partir de jobs declarativos (`src/jobs`) com origem, destino e filtros por cedente.

**Stack:** Python, paramiko, smbprotocol, pandas/openpyxl, pyodbc/SQL Server

## Destaques

- Jobs como configuração (`JobConfig`) e um runner único (`run_job.py`).
- Credenciais e destinos podem vir do banco, sobrescrevendo o job.
- Execução registrada em tabela de log.

## Estrutura

```text
file-fetch-robot/
├── scripts/
├── src/
│   ├── application/
│   │   ├── services/
│   │   └── use_cases/
│   ├── domain/
│   │   └── interfaces/
│   ├── infrastructure/
│   │   ├── config/
│   │   ├── databases/
│   │   ├── ftp/
│   │   ├── repositories/
│   │   ├── sftp/
│   │   └── smb/
│   ├── jobs/
│   ├── runners/
│   └── shared/
│       └── utils/
├── start/
└── requirements.txt
```

## Como executar

```bash
pip install -r requirements.txt
python scripts/busca_arquivo_delta.py   # um script por job
```
