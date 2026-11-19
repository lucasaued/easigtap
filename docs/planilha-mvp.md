# Uso da planilha no protótipo

Fonte única: `data/raw/Sigtap - UGPIA.xlsx`, aba `sigtap_17_06_2026`, 40 colunas e 4.984 registros. A competência junho de 2026 foi informada pelo responsável pelo projeto. O arquivo original permanece intacto.

| Dado observado | Uso no protótipo |
|---|---|
| `Procedimento` e `Descrição` | Busca por nome, palavra ou código e detalhe do procedimento. |
| `CID` e `CID Secundário` | Códigos relacionados ao procedimento, com distinção entre principal e secundário. |
| 372 registros cujo código começa por `0408` | Recorte inicial de navegação cirúrgica osteomuscular. O usuário também pode pesquisar todos os procedimentos. |
| 532 registros cujo código começa por `07` | Catálogo de itens OPM pesquisável separadamente. |
| `Qtd Máxima` em 525 dos 532 itens do grupo `07` | Teto aplicado apenas à quantidade do próprio item selecionado no protótipo. |
| `Especialidade do Leito` | Atributo administrativo; não foi usado para classificar procedimentos em Traumatologia e Ortopedia. |

A planilha não contém uma coluna com o nome do diagnóstico de cada CID nem uma coluna que identifique a compatibilidade entre uma cirurgia e um item do grupo `07`. Uma varredura das 532 linhas desse grupo não encontrou referências explícitas a códigos cirúrgicos de dez dígitos. Apenas 164 dessas linhas têm CID preenchido; 368 não têm. CIDs em comum entre linhas não comprovam compatibilidade procedimento–OPM, e a falta de CID em um item não comprova proibição.

Ao selecionar um CID, o protótipo mostra os procedimentos associados a ele e as descrições **desses procedimentos**. Ele informa quando o nome do diagnóstico CID não está disponível na fonte. A busca de itens OPM retorna somente linhas do grupo `07` que compartilham o CID selecionado e ainda podem ser refinadas por nome ou código. Esses resultados são **sugestões para avaliação**, não itens autorizados. Uma busca sem resultados também não deve ser interpretada como proibição. A quantidade máxima de um item não foi interpretada como limite específico da combinação procedimento–OPM.

O filtro `0408` é um ponto de partida para testar a navegação, não uma lista clínica definitiva de Traumatologia e Ortopedia. A base completa foi preservada para permitir que a equipe clínica identifique procedimentos adicionais e ajuste o recorte sem perder dados.
