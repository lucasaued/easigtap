# Relatório de qualidade da planilha fornecida

Arquivo: `data/raw/Sigtap - UGPIA.xlsx`. Aba: `sigtap_17_06_2026`. Inspeção local realizada com `python -m src.cli inspect-sigtap`; o relatório detalhado por linha pode ser regenerado em `data/processed/inspection.json`.

| Métrica | Resultado |
|---|---:|
| Colunas | 40 |
| Linhas de dados | 4.984 |
| Procedimentos válidos | 4.984 |
| Linhas descartadas | 0 |
| Relações CID principal | 71.238 |
| Relações CID secundário | 362 |
| CIDs distintos | 7.895 |
| Problemas CID | 31 |

Os 31 problemas são 27 itens vazios em listas e quatro códigos incompletos (`M`, `K5`, `L0`, `I2`). Os itens inválidos são omitidos da relação; os procedimentos são mantidos. Não foram encontrados códigos de procedimento ausentes, malformados ou duplicados. A coluna CID está vazia em 2.088 linhas; a CID Secundário está vazia em 4.952 linhas.

O arquivo tem duas linhas de dados a menos que as 4.986 descritas no pedido. A competência oficial não é comprovada pelo nome da aba. A planilha não contém a relação explícita procedimento–OPM, descrições oficiais completas de CID ou mapeamento validado de Traumatologia e Ortopedia.
