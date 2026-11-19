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
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m src.cli import-sigtap --file 'data/raw/Sigtap - UGPIA.xlsx' --competencia 2026-06 --origem 'Planilha fornecida ao projeto; competência informada pelo responsável'
```

Se a porta 5432 já estiver ocupada, use uma instância de teste isolada e uma URL temporária na sessão do PowerShell:

```powershell
docker run -d --rm --name easigtap-validation-pg -e POSTGRES_DB=sigtap -e POSTGRES_USER=sigtap -e POSTGRES_PASSWORD=sigtap -p 127.0.0.1:55432:5432 postgres:16-alpine
$env:DATABASE_URL='postgresql+psycopg://sigtap:sigtap@127.0.0.1:55432/sigtap'
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m src.cli import-sigtap --file 'data/raw/Sigtap - UGPIA.xlsx' --competencia 2026-06 --origem 'Planilha fornecida ao projeto; competência informada pelo responsável'
$env:EASIGTAP_TEST_DATABASE_URL=$env:DATABASE_URL
.\.venv\Scripts\python -m pytest -q -m postgres -p no:cacheprovider
```

Use esse teste apenas com um banco descartável criado para a validação. O container iniciado com `--rm` é removido ao ser parado, juntamente com seus dados não persistidos.

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

A planilha atual não fornece descrições completas de CIDs, uma coluna de compatibilidade procedimento–OPM, limites específicos dessa combinação nem uma lista revisada de procedimentos das especialidades. São necessárias conferência clínica e interpretação da fonte para completar esses pontos. `Qtd Máxima` é atributo da linha em que aparece: nas linhas do grupo `07`, o protótipo a usa como máximo do item, sem afirmar que seja o limite de sua combinação com uma cirurgia. O README público permanece breve; os procedimentos operacionais ficam neste diretório.

## Protótipo visual local

Depois de migrar e importar a planilha, execute:

```powershell
.\.venv\Scripts\python -m src.web
```

Abra `http://127.0.0.1:8000/`. O servidor escuta apenas em `127.0.0.1` por padrão. No Windows em que a porta 5432 estiver ocupada, configure `.env` com `SIGTAP_DB_PORT=55432` e `DATABASE_URL=postgresql+psycopg://sigtap:sigtap@127.0.0.1:55432/sigtap`, depois use `docker compose -p easigtap up -d --pull never db` para iniciar o banco persistente do projeto.

O recorte visual inicial usa o prefixo de código `0408`; a opção “Todos os procedimentos” mantém a busca no restante da planilha. A lista apresenta até 60 resultados por consulta, portanto refine o termo se houver mais. A busca de CID funciona por código; o clique em um CID mostra procedimentos relacionados e suas descrições. Após selecionar um CID, a busca de itens do grupo `07` é filtrada por esse CID em comum. Os itens só entram no resumo quando selecionados. Consulte [planilha-mvp.md](planilha-mvp.md) antes de interpretar esses resultados como classificações ou compatibilidades clínicas.
