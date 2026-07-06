# Model Cards - Sentinela AI

## Audio Emotion Baseline

**Objetivo:** classificar emocao vocal em clipes curtos de RAVDESS/CREMA-D.

**Modelo:** Logistic Regression com features acusticas simples.

**Features:** duracao, energia RMS, variabilidade, ZCR, pausas e clipping.

**Dados:** RAVDESS e CREMA-D indexados localmente.

**Metricas atuais:**

- Accuracy: 42.7%.
- Macro-F1: 38.7%.
- Weighted-F1: 38.7%.

**Uso apropriado:** baseline experimental de emocao vocal e componente auxiliar de sofrimento afetivo.

**Uso inadequado:** inferir diagnostico, trauma, abuso ou estado clinico.

**Limites conhecidos:**

- Datasets atuados/controlados.
- Generalizacao limitada para audio longo ou conversas reais.
- O sistema reduz confianca quando o audio esta fora do dominio de clipes curtos.

## DAiSEE Visual Wellbeing Baseline

**Objetivo:** estimar sinais visuais indiretos de bem-estar: tédio, engajamento, confusao e frustracao.

**Modelo:** RandomForest multi-output com features visuais auditaveis.

**Features:** brilho, contraste, movimento e densidade de bordas.

**Dados:** DAiSEE local, 8.571 videos indexados.

**Metricas atuais:**

- Acuracia media: 59.6%.
- Macro-F1 medio: 23.1%.

**Uso apropriado:** contexto visual indireto para bem-estar e engajamento.

**Uso inadequado:** inferir trauma, violencia, depressao ou vulnerabilidade por si so.

**Limites conhecidos:**

- Forte desbalanceamento de classes.
- Acuracia pode ser inflada por classes majoritarias.
- Macro-F1 e mais honesto que acuracia nessa base.

## Text Multi-Label Signal Baseline

**Objetivo:** extrair sinais textuais auditaveis em portugues.

**Categorias:**

- `safety_concern`
- `control_or_coercion`
- `isolation`
- `hopelessness`
- `physical_symptom`
- `psychological_distress`
- `support_network_absent`

**Modelo:** lexico + regras com normalizacao de acentos.

**Uso apropriado:** explicabilidade, triagem inicial e geracao de foco para revisao humana.

**Uso inadequado:** substituir NLP contextual ou classificar relatos sensiveis como verdade factual.

**Limites conhecidos:**

- Nao entende ironia, negacao complexa ou contexto amplo.
- Pode supervalorizar repeticoes.
- Deve evoluir para BERTimbau/embeddings contextuais.
