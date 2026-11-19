# Operação da importação SIGTAP

## Preparação no Windows PowerShell

Use Python 3.12 ou superior. A partir da raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e '.[test]'
.\.venv\Scripts\python -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python -m src.cli inspect-sigtap --file 'data/raw/Sigtap - UGPIA.xlsx' --report data/processed/inspection.json
```

`data/processed/inspection.json` contém os problemas por linha e é ignorado pelo Git. O arquivo de entrada e o relatório resumido estão descritos em [data-quality.md](data-quality.md).

## PostgreSQL

O `docker-compose.yml` prepara um PostgreSQL local. Antes de importar, confirme que o serviço está disponível:

```powershell
docker compose up -d db
Copy-Item .env.example .env
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\python -m src.cli import-sigtap --file 'data/raw/Sigtap - UGPIA.xlsx' --competencia 2026-06 --origem 'Planilha fornecida ao projeto; competência informada pelo responsável'
```

A importação da mesma combinação de competência e SHA-256 é idempotente. Outra planilha para a mesma competência é recusada. O status `validado_tecnicamente` significa apenas que a inspeção não encontrou erros; `importado_com_pendencias` indica erros de entrada não fatais. Nenhum desses estados significa conferência com o SIGTAP oficial. A migração `0002` converte os antigos estados `validado` e `parcial`, normaliza as chaves CID e guarda a grafia original das relações existentes. Faça backup do banco antes de aplicar migrações em dados que precisem ser preservados.

Para conferir uma carga em PostgreSQL, execute:

```sql
SELECT version_num FROM alembic_version;
SELECT referencia, status, sha256, origem FROM competencias;
SELECT count(*) FROM procedimentos;
SELECT tipo, count(*) FROM procedimento_cid GROUP BY tipo;
SELECT count(*) FROM cids;
SELECT count(*) FROM opms;
SELECT count(*) FROM procedimento_opm;
SELECT count(*) FROM especialidade_procedimento;
SELECT extname FROM pg_extension WHERE extname IN ('unaccent', 'pg_trgm');
SELECT indexname FROM pg_indexes WHERE tablename IN ('procedimentos', 'cids');
SELECT count(*) FROM procedimento_cid pc LEFT JOIN procedimentos p ON p.id = pc.procedimento_id LEFT JOIN cids c ON c.id = pc.cid_id WHERE p.id IS NULL OR c.id IS NULL;
SELECT sigtap_search('FÊMUR');
```

Consulte também o comportamento de importação repetida, competência diferente e rollback em transação de teste. Não publique um resultado como validado em PostgreSQL sem executar essas verificações nesse banco.

## Dados pendentes

A planilha atual não fornece descrições completas de CIDs, compatibilidades procedimento–OPM, limites de OPM nem uma lista revisada de procedimentos das especialidades. São necessárias fontes confiáveis e conferência clínica para completar esses campos. `Qtd Máxima` da planilha é atributo do procedimento e não deve ser usada como limite de OPM. O README público permanece breve; os procedimentos operacionais ficam neste diretório.
