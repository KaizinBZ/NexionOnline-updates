# Índice de veículos

| Pasta | Arquivos | ID declarado/encontrado | Observação |
|---|---|---:|---|
| `SW4/` | `bf.dff`, `bf.txd` | **424** | Carregador nativo SW4 do APK; substitui o BF Injection. |
| `427-BOPEBlindado/` | `enforcer.dff`, `enforcer.txd` | **427** | ID declarado no `script.lua` do pacote BOPE Blindado. |
| `445-PRFVTR1/` | `rancher.dff`, `rancher.txd` | **445** | ID declarado no `script.lua` do pacote PRF VTR1. |
| `400-FordRaptor/` | `FordRaptor.dff`, `FordRaptor.txd` | **400** | ID declarado no `script.lua` do pacote Ford Raptor. |
| `unknown-Turquia/` | `turquia.dff`, `turquia.txd` | **não identificado** | O arquivo enviado não contém `meta.xml` nem `script.lua`; não atribuí um ID por suposição. |

Os três primeiros IDs foram lidos diretamente dos scripts MTA enviados. Esses arquivos continuam organizados como recursos de veículos; o carregador SW4 nativo do APK, especificamente, usa apenas `SW4/bf.dff` e `SW4/bf.txd` no ID 424. Os recursos MTA com `meta.xml`/`script.lua` não são executados diretamente pelo cliente Android nativo.

## Conteúdo original dos scripts

- `enforcer.dff`/`enforcer.txd`: `engineReplaceModel(..., 427)`.
- `rancher.dff`/`rancher.txd`: `engineReplaceModel(..., 445)`.
- `FordRaptor.dff`/`FordRaptor.txd`: `engineReplaceModel(..., 400)`.
- `turquia.dff`/`turquia.txd`: nenhum script de instalação enviado.
