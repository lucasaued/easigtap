# Relatório de qualidade da planilha fornecida

Arquivo: `data/raw/Sigtap - UGPIA.xlsx`. Aba: `sigtap_17_06_2026`. Inspeção local repetida com o ambiente isolado e `python -m src.cli inspect-sigtap`; o relatório detalhado por linha pode ser regenerado em `data/processed/inspection.json`. SHA-256 do arquivo: `b35c88d5dd88b749157c6a4ec34f2ece2dd96267785f9840f5b803d5e38d39b4`.

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

O arquivo tem duas linhas de dados a menos que as 4.986 descritas para outra versão da planilha em conversa anterior. O responsável pelo projeto confirmou **junho de 2026** como competência desta planilha em 19/11/2026; essa confirmação foi informada pelo operador e não constitui comparação independente com o pacote oficial do SIGTAP. A planilha não contém a relação explícita procedimento–OPM, descrições oficiais completas de CID ou mapeamento validado de Traumatologia e Ortopedia.

Os códigos CID são armazenados em uma chave de busca sem ponto e em maiúsculas, mantendo a grafia da planilha em `procedimento_cid.codigo_original`. Essa normalização não confirma a existência dos códigos em um catálogo oficial. Após a carga, o status é `importado_com_pendencias` devido aos 31 problemas acima, sem alegação de validação oficial.
