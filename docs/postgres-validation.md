# Validação em PostgreSQL

Executada em 19/11/2026 em um container isolado `postgres:16-alpine` na porta local 55432. A porta 5432 estava ocupada por outro projeto; esse banco não foi acessado. A base de validação não é um ambiente de produção.

## Migração e carga

- `python -m alembic upgrade head` chegou à revisão `0002_cid_normalization_status`.
- `python -m src.cli import-sigtap --file 'data/raw/Sigtap - UGPIA.xlsx' --competencia 2026-06 ...` importou 4.984 procedimentos e 71.600 relações.
- Uma segunda execução com o mesmo arquivo e competência retornou `already_imported`, com zero registros novos.
- A planilha possui 31 problemas em entradas CID; o status da carga é `importado_com_pendencias` e `validacao_oficial` permanece `false`.

| Conferência direta no PostgreSQL | Resultado |
|---|---:|
| Competências | 1 |
| Procedimentos | 4.984 |
| CIDs distintos | 7.895 |
| Relações CID principal | 71.238 |
| Relações CID secundário | 362 |
| Relações sem procedimento ou CID | 0 |
| Relações sem grafia CID original | 0 |
| OPMs e relações procedimento–OPM | 0 |
| Classificações de especialidade | 0 |

As extensões `unaccent` e `pg_trgm` e os índices de busca foram encontrados. A busca `sigtap_search(nome) LIKE '%femur%'` retornou 25 procedimentos. O CID normalizado `S720` tinha um único cadastro e 31 relações consultáveis no sentido CID → procedimento.

## Falhas e atualização de base anterior

- Uma importação de teste em outra competência, executada dentro de uma transação que gerou uma falha simulada, foi revertida. A base permaneceu com uma competência e 4.984 procedimentos.
- Em um segundo banco descartável, uma estrutura da revisão `0001` foi preparada com os campos antigos e CIDs `S72.0` e `S720`. Após `upgrade head`, restou a chave `S720`; as grafias originais das duas relações foram preservadas e o status antigo `validado` passou a `validado_tecnicamente`.
- O teste automatizado de integração somente leitura está em `tests/test_postgres_integration.py` e requer `EASIGTAP_TEST_DATABASE_URL` para um banco de teste já migrado e carregado.

Estas verificações comprovam o comportamento técnico nessa instância PostgreSQL. Não substituem a comparação com os arquivos oficiais do SIGTAP nem a validação clínica das relações.
