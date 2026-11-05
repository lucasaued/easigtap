# EasiGTAP — Entrega 1

Camada de dados para consulta futura da tabela SIGTAP no HUSM/UFSM. Esta etapa lê a planilha, valida procedimentos e CIDs, preserva a origem e prepara as tabelas de OPM e especialidades. Não inclui API nem interface.

## Requisitos e instalação

Python 3.12+, PostgreSQL 16+ e Docker Compose opcional. A planilha fornecida está em `data/raw/Sigtap - UGPIA.xlsx` (nome diferente do previsto na especificação).

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
Copy-Item .env.example .env
docker compose up -d db
python -m alembic upgrade head
```

Se usar PostgreSQL já instalado, ajuste `DATABASE_URL` em `.env`. A migração cria `unaccent`, `pg_trgm` e índices de busca; o usuário do banco precisa de permissão para criar essas extensões.

## Inspeção e importação

Confirme a competência com a fonte responsável antes da importação. O nome da aba não a confirma.

```powershell
python -m src.cli inspect-sigtap --file "data/raw/Sigtap - UGPIA.xlsx" --report data/processed/inspection.json
python -m src.cli import-sigtap --file "data/raw/Sigtap - UGPIA.xlsx" --competencia YYYY-MM --origem "Identificação confirmada da fonte" --report data/processed/import.json
python -m pytest
```

O relatório JSON contém hash, aba, cabeçalhos, contagens, campos vazios e problemas por linha. Linhas com procedimento inválido ou duplicado são ignoradas; CIDs malformados são registrados e ignorados isoladamente. Qualquer falha no banco reverte a transação. Repetir o mesmo arquivo e competência não duplica dados. Um arquivo diferente para a mesma competência é recusado, preservando a versão já importada.

## Especialidades e OPM

`data/specialidades.csv` é um modelo vazio. Após revisão por especialista, preencha competência, código, especialidade (`Traumatologia` ou `Ortopedia`) e fonte de validação. Importe com:

```powershell
python -m src.cli import-specialties --file data/specialidades.csv
```

As tabelas OPM e procedimento–OPM ficam vazias até existir fonte oficial. O contrato em `src/importers/opm_contract.py` exige identificação e fonte e admite limite desconhecido (`NULL`). `Qtd Máxima` permanece atributo do procedimento e não define limite de OPM.

## Consultas SQL

```sql
SELECT codigo, nome FROM procedimentos WHERE codigo = '0408040122';
SELECT codigo, nome FROM procedimentos WHERE sigtap_search(nome) LIKE '%femur%';
SELECT p.codigo, p.nome, pc.tipo FROM procedimentos p
JOIN procedimento_cid pc ON pc.procedimento_id = p.id
JOIN cids c ON c.id = pc.cid_id WHERE c.codigo = 'S720';
SELECT codigo, descricao FROM cids WHERE sigtap_search(descricao) LIKE '%fratura%';
```

Para aproveitar o índice trigram, consultas com substring podem usar `LIKE '%termo%'` sobre `sigtap_search(nome)`. A função é imutável para indexação; após atualização do dicionário `unaccent`, recrie os índices de busca.

## Estrutura e limitações

- `src/parsers`: separação de procedimento e CID.
- `src/importers`: inspeção, persistência e classificação revisada.
- `src/database`: modelos e conexão; `alembic`: migração.
- `tests`: parsers e integração de persistência em SQLite. A migração e a busca PostgreSQL exigem um servidor PostgreSQL para validação completa.
- A planilha real tem 4.984 registros, não 4.986 como informado no pedido. A inspeção encontrou 31 problemas em entradas CID, incluindo itens vazios em listas e um código malformado; todos os 4.984 procedimentos são válidos. A competência ainda precisa de confirmação externa.
- A planilha não traz descrições oficiais completas de CID nem relações explícitas procedimento–OPM. A busca por nome de diagnóstico depende da futura carga oficial de CID-10. O mapeamento definitivo de Traumatologia e Ortopedia depende de revisão especializada. Nenhuma regra clínica ou limite de OPM é inferido.

Próxima etapa de dados: obter fontes oficiais de CID-10, OPM e regras de compatibilidade com competência e proveniência verificáveis.
