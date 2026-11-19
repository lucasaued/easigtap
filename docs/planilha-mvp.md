# Uso das fontes no protótipo

Fonte inicial: `data/raw/Sigtap - UGPIA.xlsx`, aba `sigtap_17_06_2026`, 40 colunas e 4.984 registros. A competência junho de 2026 foi informada pelo responsável pelo projeto. O arquivo original permanece intacto. A base recebeu complemento do pacote oficial SIGTAP de junho de 2026, descrito em [operacao.md](operacao.md).

| Dado observado | Uso no protótipo |
|---|---|
| `Procedimento` e `Descrição` | Busca por nome, palavra ou código e detalhe do procedimento. |
| `CID` e `CID Secundário` | Códigos relacionados ao procedimento, com distinção entre principal e secundário. |
| 372 registros cujo código começa por `0408` | Recorte inicial de navegação cirúrgica osteomuscular. O usuário também pode pesquisar todos os procedimentos. |
| 532 registros cujo código começa por `07` | Catálogo de itens OPM. A seleção por procedimento usa as compatibilidades do pacote oficial. |
| `Qtd Máxima` em 525 dos 532 itens do grupo `07` | Atributo da planilha preservado, mas não usado como limite da relação procedimento–OPM. |
| `Especialidade do Leito` | Atributo administrativo; não foi usado para classificar procedimentos em Traumatologia e Ortopedia. |

A planilha não contém uma coluna com o nome do diagnóstico de cada CID nem uma coluna que identifique a compatibilidade entre cirurgia e OPM. O pacote oficial fornece os nomes em `tb_cid.txt` e as relações em `rl_procedimento_compativel.txt`. A ausência de CID em 368 linhas de OPM da planilha não interfere na consulta das relações oficiais.

Ao selecionar um CID, o protótipo mostra seu nome oficial e os procedimentos associados na planilha. A busca de OPM retorna apenas itens com relação de compatibilidade registrada no SIGTAP 06/2026 para o procedimento selecionado, refináveis por nome ou código. O CID escolhido não altera essa relação. A quantidade máxima exibida vem de `QT_PERMITIDA` da compatibilidade. Uma busca sem resultados não é, por si só, decisão sobre uso clínico, condições de registro ou proibição.

O filtro `0408` é um ponto de partida para testar a navegação, não uma lista clínica definitiva de Traumatologia e Ortopedia. A base completa foi preservada para permitir que a equipe clínica identifique procedimentos adicionais e ajuste o recorte sem perder dados.
