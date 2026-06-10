#!/usr/bin/env bash
# =============================================================================
# seed-issues.sh — cria milestones + issues a partir de docs/initial-issues.md
#
# ⚠️  RODAR SÓ APÓS `git push` E `gh auth login`. NÃO é executado pelo scaffold.
#
# Idempotente: milestones e issues já existentes (mesmo título) são pulados.
# Requer: gh CLI autenticado, repo com remote no GitHub.
# =============================================================================
set -euo pipefail

REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
echo "Repo alvo: ${REPO}"

# --- milestones ---------------------------------------------------------------
MILESTONES=(
  "Gate Zero (pré-registro)"
  "Test 1 — Reconstrução (fev+out)"
  "Test 2 — Posicionamento (Morpho+integrador)"
  "Test 3 — Rampa"
  "Semana 4 — Veredito"
)

existing_milestones="$(gh api "repos/${REPO}/milestones?state=all&per_page=100" -q '.[].title')"

for m in "${MILESTONES[@]}"; do
  if grep -Fxq "$m" <<<"$existing_milestones"; then
    echo "milestone já existe, pulando: $m"
  else
    gh api "repos/${REPO}/milestones" -f title="$m" >/dev/null
    echo "milestone criado: $m"
  fi
done

# --- issues -------------------------------------------------------------------
# create_issue <milestone> <título> <corpo>
existing_issues="$(gh issue list --state all --limit 200 --json title -q '.[].title')"

create_issue() {
  local milestone="$1" title="$2" body="$3"
  if grep -Fxq "$title" <<<"$existing_issues"; then
    echo "issue já existe, pulando: $title"
  else
    gh issue create --title "$title" --body "$body" --milestone "$milestone" >/dev/null
    echo "issue criada: $title"
  fi
}

M1="Gate Zero (pré-registro)"
create_issue "$M1" "Preencher thresholds do § 4 do pré-registro" \
  "Decisão humana dos limiares FORTE/MÉDIO/FRACO, ABERTO/CONTESTADO/FECHADO, TEM/FINA/SEM, antes de qualquer dado. Ver docs/initial-issues.md."
create_issue "$M1" "Commit + push separado e rotulado do pré-registro" \
  "Usar a mensagem de commit do CONTRIBUTING.md; nenhum outro arquivo no commit."
create_issue "$M1" "Ancorar o pré-registro externamente" \
  "OpenTimestamps no arquivo e/ou hash do commit postado publicamente (fórum Morpho / X)."

M2="Test 1 — Reconstrução (fev+out)"
create_issue "$M2" "Resolver fonte de preço de oráculo histórico por bloco" \
  "Nó arquival vs. feed do provedor; risco nº 1 de cronograma (§ 3.3 do plano)."
create_issue "$M2" "Reconstruir 5–10 liquidações de fev/2026 (3 camadas)" \
  "Janela teórica, janela realizada point-in-time, atribuição capacidade vs. consciência."
create_issue "$M2" "Checagem out-of-sample em out/2025" \
  "Repetir a reconstrução no flash crash; comparar estabilidade entre regimes."
create_issue "$M2" "Redigir e publicar a peça de pesquisa" \
  "Fórum Morpho + X + Dune, referenciando o hash do commit do pré-registro."

M3="Test 2 — Posicionamento (Morpho+integrador)"
create_issue "$M3" "Conversa com Morpho (fórum/BD)" \
  "Estratégia oficial de risk tooling retail/integrador-facing e posição vs. Hypernative."
create_issue "$M3" "Call com ≥1 integrador (warm intro)" \
  "Build-vs-buy de terceiro neutro; o que faltou em fevereiro."
create_issue "$M3" "Pedir dado de alert-delivery ao integrador" \
  "Refina o teto endereçável removendo 'viu e declinou'."

M4="Test 3 — Rampa"
create_issue "$M4" "Inventariar 20 contatos em integradores Morpho" \
  "Por grau (direto/2º/zero) e por função (risco/lending/eng)."
create_issue "$M4" "Classificar a rampa (TEM/FINA/SEM)" \
  "Contra os limiares pré-registrados."

M5="Semana 4 — Veredito"
create_issue "$M5" "Consolidar os 3 sinais contra a matriz de decisão" \
  "Sinal × Espaço, Rampa modulando execução."
create_issue "$M5" "Registrar o veredito GO/NO-GO/Pivô" \
  "Documento curto com expectativa (§ 1 do pré-registro) vs. observado."

echo "Concluído."
