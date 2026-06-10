# LICENSING

Este é um monorepo de **licença mista**. A licença que governa cada arquivo é a do seu diretório, conforme a tabela abaixo — não o rótulo único que o GitHub exibir.

| Diretório | Licença | Arquivo |
|---|---|---|
| `packages/ingestion/` | **MIT** | `LICENSE-MIT` |
| `dune/` | **MIT** | `LICENSE-MIT` |
| `quant/` | **BUSL-1.1** (Change License: Apache-2.0) | `LICENSE-BSL` |
| Demais arquivos (docs, configs, raiz) | **MIT** | `LICENSE-MIT` |

## Racional do split

- **Infra-commodity** (ingestão, queries Dune, helpers) → **MIT**: maximiza adoção e auditabilidade; não é onde está a defensibilidade.
- **Modelo de risco** (`quant/`) → **BUSL-1.1** (source-available): código aberto para leitura e avaliação, mas com restrição de uso em produção até a Change Date, quando converte para **Apache-2.0**. Precedente direto: o core do Morpho Blue é BUSL-1.1.

Parâmetros do BUSL (Licensor, Change Date etc.) estão em `LICENSE-BSL`. O Additional Use Grant permite uso limitado a **pesquisa não-produtiva e avaliação interna**.

## Nota sobre o rótulo do GitHub

O GitHub detecta licença por heurística e pode rotular este repo de forma imprecisa (ex.: exibir só "MIT" ou "licença não detectada") por ser monorepo de licença mista. **Quem governa são os arquivos de licença por diretório e esta tabela**, não o rótulo da interface.

## Headers

Arquivos-fonte de `quant/` levam header BUSL-1.1; arquivos-fonte de `packages/ingestion/` levam header MIT.
