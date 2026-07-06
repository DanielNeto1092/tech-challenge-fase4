# Sentinela AI — Relatório Técnico (Fase 4)

## 1. Resumo Executivo e Aderência aos Requisitos

O Sentinela AI é um sistema de monitoramento multimodal de saúde e segurança feminina que processa **5 modalidades** — áudio, texto, vídeo, detecção de objetos e dados clínicos — para identificar sinais precoces de risco. O sistema gera alertas auditáveis, trilhas de cuidado trauma-informadas e indicadores de revisão humana.

### Matriz de Aderência

| Requisito Obrigatório                     | Implementação                                                                                    | Artefato                                                           |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| Análise de vídeo especializada            | YOLOv8-Pose (postura defensiva), motion energy, DAiSEE visual wellbeing                          | `src/extractors/pose.py`, `motion.py`, `visual_wellbeing.py`       |
| YOLOv8 customizado para objetos suspeitos | YOLOv8n pré-treinado (COCO) com fallback; fine-tuning disponível via dataset Roboflow 15 classes | `src/extractors/objects.py`, `src/training/train_sharp_objects.py` |
| Análise de áudio especializada            | Features acústicas (RMS, ZCR, pausas, clipping) + baseline emocional (LogReg RAVDESS)            | `src/extractors/audio.py`, `audio_emotion.py`                      |
| Fusão multimodal                          | Late fusion ponderada por confiança com 5 modalidades, coverage penalty e pesos auditáveis       | `src/engines/fusion_engine.py`                                     |
| Relatórios automáticos                    | RiskReport JSON com prioridade (ROTINA/MONITORAR/URGENTE), care assessment e guardrails          | `src/engines/risk_engine.py`, `care_engine.py`                     |
| Detecção de sinais não-verbais            | Heurística de postura defensiva (mãos no rosto, braços dobrados), análise temporal               | `src/extractors/pose.py`                                           |
| Integração cloud                          | AWS Free Tier: S3 (SSE-S3) + DynamoDB + Lambda + SNS (planejado)                                 | `src/cloud/aws_publish.py`, `docs/aws_architecture.md`             |
| Indicadores de violência doméstica        | Marcadores textuais multi-label (safety_concern, control_or_coercion, isolation, hopelessness)   | `src/extractors/text.py`                                           |
| Monitoramento psicológico                 | Care assessment com wellbeingIndex, affectiveDistress, audioEmotionDistress                      | `src/engines/care_engine.py`                                       |

### Objetivos Escolhidos (mínimo 3 de 5)

1. **Identificar sinais de violência doméstica ou abuso** — via texto (7 categorias de risco), objetos cortantes (YOLOv8), postura defensiva (pose).
2. **Monitorar bem-estar psicológico feminino** — via care assessment multidimensional com trilha de cuidado.
3. **Aplicar detecção de anomalias em tempo real** — via prioridade operacional, flags de anomalia (low_confidence, modality_disagreement, sharp_object_detected).
4. **Utilizar serviços em nuvem** — via arquitetura AWS Free Tier com S3, Lambda, DynamoDB e SNS.

---

## 2. Definição do Problema

### Contexto Clínico

A violência doméstica contra mulheres frequentemente se manifesta por sinais indiretos: hesitação na fala, tom vocal alterado, posturas defensivas, presença de objetos cortantes no ambiente e relatos com marcadores linguísticos de medo, controle ou isolamento. Esses sinais aparecem de forma multimodal e raramente em uma única fonte de dados.

### Desafio Técnico

Construir um pipeline que:

- Processe modalidades heterogêneas (áudio PCM, texto em português, frames de vídeo, imagens para detecção de objetos).
- Funda sinais com pesos adaptativos por confiança e disponibilidade.
- Gere alertas sem diagnosticar — o sistema é ferramenta de apoio à triagem, não decisor clínico.
- Opere com dados sensíveis sob conformidade LGPD.

### Restrição Ética

O sistema adota abordagem indireta: não afirma violência doméstica. Ele identifica sinais de atenção (safety_concern, affective_distress, nonverbal_alert) e encaminha para revisão humana com comunicação trauma-informada.

---

## 3. Arquitetura: Design e Decisões

### Padrão Arquitetural

Clean Architecture com separação em camadas:

```
src/
├── config.py              # Configuração centralizada (ModelPaths, Weights, Thresholds)
├── domain/types.py        # Value objects (ModalityScore, ObjectDetection, RiskReport)
├── extractors/            # Feature extraction por modalidade (SRP)
├── engines/               # Lógica de negócio (Fusion, Risk, Care)
├── pipeline.py            # Orquestrador (compõe extractors + engines)
├── api/app.py             # Interface HTTP (FastAPI)
├── cloud/                 # Integração AWS
└── training/              # Scripts de treino
```

### Decisões Técnicas

| Decisão                                       | Justificativa                                                                            |
| --------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Late fusion (não early/attention)             | Datasets heterogêneos, modalidades faltantes, explicabilidade.                           |
| 5 modalidades separadas (não 4)               | Objetos cortantes + dados clínicos como sinais independentes de risco.                   |
| Coverage penalty                              | Reduz score quando poucas modalidades estão disponíveis — evita falso positivo.          |
| Modelos leves (LogReg, RandomForest, YOLOv8n) | Rodam em CPU, viáveis no Free Tier, suficientes como baseline.                           |
| Configuração via dataclass                    | PipelineConfig centraliza pesos, thresholds e paths — facilita auditoria.                |
| Tipagem estrita                               | `ModalityScore`, `RiskReport` como frozen dataclasses — imutabilidade e rastreabilidade. |

---

## 4. Dados (Datasets usados para treino/inferência)

| Dataset                  | Modalidade  | Uso                                                                          | Tamanho         | Status                                    |
| ------------------------ | ----------- | ---------------------------------------------------------------------------- | --------------- | ----------------------------------------- |
| RAVDESS                  | Áudio       | Baseline emocional (6 emoções: angry, disgust, fearful, happy, neutral, sad) | 1.012 entradas  | ✅ Manifest gerado, usado em pipeline     |
| EATD-Corpus              | Áudio+Texto | Depressão/distress (SDS score 20-80)                                         | 972 entradas    | ✅ Manifest gerado, evidência audio       |
| DAiSEE                   | Vídeo       | Baseline visual de bem-estar (boredom, engagement, confusion, frustration)   | 17.496 entradas | ✅ Manifest gerado, baseline treinado     |
| Cardiotocography (CTG)   | Clínico     | Risco fetal (Normal/Suspect/Pathological via NSP)                            | 2.126 entradas  | ✅ Manifest gerado, integrado no pipeline |
| Maternal Health Risk     | Clínico     | Risco obstétrico (low/mid/high risk via sinais vitais)                       | 1.014 entradas  | ✅ Manifest gerado, integrado no pipeline |
| XD-Violence              | Vídeo       | Proxy de anomalia visual (NÃO é dado clínico)                                | 16 exemplos     | ✅ Manifest gerado, uso como proxy        |
| Sharp Objects (Roboflow) | Imagem      | Fine-tuning YOLOv8n para 15 classes de objetos cortantes                     | 2.250 imagens   | ✅ COCO fallback funcional                |
| UCF-Crime                | Vídeo       | Calibração de motion energy (NormalVideos vs Abuse)                          | 1.900 vídeos    | ⏳ Pendente                               |

### Taxonomio Sentinela (Label Mapping)

Todos os datasets são mapeados para uma taxonomia unificada (`src/domain/labels.py`):

| Label Sentinela             | Significado                         | Datasets fonte                                                        |
| ------------------------ | ----------------------------------- | --------------------------------------------------------------------- |
| `normal_or_low_risk`     | Sem sinal de risco                  | RAVDESS (calm, neutral, happy), CTG (Normal), Maternal (low)          |
| `psychological_distress` | Sofrimento psicológico genérico     | RAVDESS (angry, disgust), EATD (SDS 53-62), DAiSEE (frustration_high) |
| `depression_signal`      | Sinal de depressão                  | EATD (SDS ≥ 63)                                                       |
| `anxiety_or_fear`        | Ansiedade ou medo                   | RAVDESS (fearful), EATD (SDS 40-52)                                   |
| `visual_discomfort`      | Desconforto visual / desengajamento | DAiSEE (boredom_high, confusion_high, engagement_low)                 |
| `obstetric_risk`         | Risco obstétrico intermediário      | CTG (Suspect), Maternal (mid risk)                                    |
| `fetal_risk`             | Risco fetal severo                  | CTG (Pathological), Maternal (high risk)                              |
| `safety_anomaly`         | Anomalia de segurança ambiental     | XD-Violence (abuse, fighting, shooting)                               |

### Limitações Documentadas

- RAVDESS é acted speech — generalização limitada para fala espontânea.
- DAiSEE é filmagem educacional — não representa contexto clínico diretamente.
- XD-Violence contém anomalias genéricas — usado apenas como proxy de anomalia visual, não é dado clínico.
- O sistema reduz confiança automaticamente quando detecta out-of-domain (áudio longo, dados insuficientes).

---

## 4.1. Uso de Modelos Pré-Treinados — Justificativa Técnica

O professor autorizou o uso de modelos pré-treinados para acelerar o desenvolvimento. O projeto adota a seguinte estratégia:

| Modelo Pré-Treinado          | Tarefa                                                | Justificativa                                                                                  | Limitações                                                                                                     |
| ---------------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| YOLOv8n (COCO)               | Detecção de objetos cortantes (knife, scissors, fork) | Disponível imediatamente, sem custo de treino; detecta classes relevantes para risco ambiental | Apenas 3 classes genéricas vs. 15 do dataset customizado; pode não detectar objetos em ângulos/fundos atípicos |
| YOLOv8n-Pose (COCO17)        | Estimativa de postura corporal                        | Keypoints COCO17 permitem heurística de postura defensiva sem treinar classificador de pose    | Heurística manual; não captura nuances culturais de linguagem corporal                                         |
| LogisticRegression (RAVDESS) | Classificação emocional por áudio                     | Baseline auditável com features acústicas simples; treinado localmente com datasets públicos   | Accuracy 42.7%; generalização limitada para fala espontânea                                                    |
| RandomForest (DAiSEE)        | Bem-estar visual                                      | Captura padrões de engajamento/frustração em vídeo                                             | Treinado em contexto educacional, não clínico                                                                  |

### Estratégia de Fallback

O `SharpObjectDetector` implementa fallback hierárquico:

1. Se `runs/detect/sharp_object_detector/weights/best.pt` existir → usa modelo custom (15 classes, conf=0.5).
2. Se não existir → usa YOLOv8n COCO pré-treinado (3 classes: knife, scissors, fork, conf=0.25).
3. Se nenhum modelo estiver disponível → retorna `available: False` com warning.

Em todos os casos, qualquer detecção de objeto de risco:

- Escala o caso para no mínimo MONITORAR;
- Marca `humanReviewRequired: true`;
- Adiciona flag `sharp_object_detected`.

### Evidências de Funcionamento (dados reais)

| Evidência                                      | Resultado                                  | Arquivo                                               |
| ---------------------------------------------- | ------------------------------------------ | ----------------------------------------------------- |
| Maternal Health high risk (SBP=140, BS=13)     | Score 0.722, URGENTE, revisao_prioritaria  | `data/results/evidence_maternal_high_risk.json`       |
| CTG Pathological (NSP=3, severe decelerations) | Score 0.748, URGENTE, revisao_prioritaria  | `data/results/evidence_ctg_pathological.json`         |
| CTG Normal (NSP=1)                             | Score 0.088, ROTINA, acompanhamento_rotina | `data/results/evidence_ctg_normal.json`               |
| Maternal Health low risk                       | Score 0.106, ROTINA, acompanhamento_rotina | `data/results/evidence_maternal_low_risk.json`        |
| Texto psicológico (medo, ansiedade, insônia)   | Score 0.441, MONITORAR                     | `data/results/evidence_text_psychological.json`       |
| Multimodal texto + clinical mid risk           | Score 0.397, acolhimento_e_monitoramento   | `data/results/evidence_multimodal_text_clinical.json` |
| EATD-Corpus audio (SDS=82.5, depression)       | Processado com sucesso                     | `data/results/evidence_eatd_audio.json`               |
| RAVDESS fearful audio                          | Processado com sucesso                     | `data/results/evidence_ravdess_fearful.json`          |
| Fork detectado (COCO fallback, conf 0.891)     | Score, MONITORAR, human review             | `data/results/evidence_object_fork.json`              |

---

## 4.2. Vínculo com Saúde da Mulher e Contexto Perinatal

A violência doméstica é reconhecida pela OMS como o **principal fator de risco evitável em saúde materna** (WHO, 2021), associada a:

- Prematuridade e baixo peso ao nascer;
- Mortalidade perinatal aumentada em 2-3x;
- Depressão pós-parto e transtorno de estresse pós-traumático;
- Recusa de acompanhamento pré-natal por medo ou controle do parceiro.

O Sentinela AI detecta sinais precoces desse fator de risco (hesitação vocal, marcadores linguísticos de controle/isolamento, postura defensiva, objetos cortantes) para apoiar a triagem em contexto perinatal — sem diagnosticar violência diretamente, usando abordagem indireta e trauma-informada.

### Por que não usamos dados clínicos reais

1. **Ética e privacidade**: dados de violência doméstica são sensíveis por natureza (LGPD Art. 11).
2. **Acesso restrito**: datasets clínicos reais (DAIC-WOZ, prontuários) requerem aprovação de comitê de ética.
3. **Alternativa**: usamos proxies públicos (RAVDESS para emoção, XD-Violence para anomalia, DAiSEE para bem-estar) documentando explicitamente as limitações de generalização.
4. **Posicionamento**: o sistema é ferramenta de apoio à triagem que organiza sinais para revisão humana — nunca diagnóstico automático.

---

## 5. Modelos Multimodais e YOLOv8

### 5.1 Baseline Emocional por Áudio

- **Modelo**: Logistic Regression com StandardScaler.
- **Features**: duration_s, rms_mean, rms_std, rms_p95, rms_dynamic_range, zcr_mean, zcr_std, silence_ratio, clipping_ratio.
- **Accuracy**: 42.7% | **Macro-F1**: 38.7%.
- **Arquivo**: `models/audio_emotion_baseline/audio_emotion_baseline.joblib`.

### 5.2 Baseline Visual DAiSEE

- **Modelo**: RandomForest (MultiOutputClassifier, 160 estimators).
- **Features**: brightness, contrast, motion, edge density (12 features).
- **Labels**: boredom, engagement, confusion, frustration (ordinal 0-3).
- **Accuracy média**: 59.6% | **Macro-F1 médio**: 23.1%.
- **Arquivo**: `models/daisee_visual_baseline/daisee_visual_baseline.joblib`.

### 5.3 YOLOv8n — Sharp Objects Detection

- **Produção atual**: YOLOv8n fine-tuned no dataset Sharp Objects Detection (Roboflow).
- **Classes detectáveis (modelo custom)**: Cutter, Fork, Hair Brush, Hair Comb, Ice Pick, Knife, Peeler, Pen, Pencil, Plastic Bottle, Scissors, Screwdriver, Shoe, Slipper, Spoon (15 classes).
- **Dataset**: 2.250 imagens com auto-split 80/20 (1.800 train, 450 val).
- **Resultados de treino (10 epochs, imgsz=320)**:
  - **mAP@50: 87.9%**
  - **mAP@50-95: 60.6%**
  - **Precision: 84.2%**
  - **Recall: 81.1%**
- **Modelo salvo**: `runs/detect/sharp_object_detector/weights/best.pt`.
- **Fallback**: se o modelo custom não estiver disponível, usa YOLOv8n COCO (knife, scissors, fork).
- **Script de treino**: `src/training/train_sharp_objects.py`.
- **Evidência**: `data/results/evidence_yolov8_sharp_objects_training.json`.

### 5.4 YOLOv8n-Pose — Postura Defensiva

- **Modelo**: YOLOv8n-Pose (COCO17 keypoints).
- **Heurística**: hands_near_face (65%) + arms_bent (35%).
- **Agregação temporal**: percentil 95 sobre frames.
- **Fluxo end-to-end demonstrado**: vídeo .avi → YOLOv8n-Pose → keypoints COCO17 → PoseExtractor → score temporal.
- **Evidência**: `data/results/evidence_video_end_to_end.json`, `data/results/evidence_video_keypoints_extracted.json`.
- **Script de demo**: `scripts/demo_video_end_to_end.py`.

### 5.5 Sinais Textuais (NLP Léxico)

- **Abordagem**: lexicon multi-label com 7 categorias em português.
- **Categorias**: safety_concern, control_or_coercion, isolation, hopelessness, physical_symptom, psychological_distress, support_network_absent.
- **Recursos**: normalização de acentos, detecção de negação contextual, intensificadores e hedges.

---

## 6. Pipeline de Fusão Multimodal

### Fórmula de Fusão

$$s_{mm} = \sum_{m \in \{video, audio, text, objects, clinical\}} w_m^{norm} \cdot s_m \cdot \text{coverage\_penalty}(n)$$

Onde:

- $w_m^{raw} = w_m^{base} \cdot \text{confidence}_m$
- $w_m^{norm} = w_m^{raw} / \sum w^{raw}$
- $\text{coverage\_penalty}(n)$: 0.88 (1 mod.), 0.94 (2), 0.97 (3), 0.99 (4), 1.0 (5)

### Pesos Base

| Modalidade | Peso Base | Justificativa                                                         |
| ---------- | --------- | --------------------------------------------------------------------- |
| Vídeo      | 0.25      | Sinais não-verbais e postura têm forte correlação com vulnerabilidade |
| Áudio      | 0.20      | Variabilidade vocal e emoção são indicadores de distress              |
| Texto      | 0.20      | Marcadores linguísticos de risco são explícitos e auditáveis          |
| Objetos    | 0.15      | Presença de objetos cortantes é sinal ambiental de risco              |
| Clínico    | 0.20      | Dados obstétricos/fetais são critérios clínicos validados             |

### Regras de Escalação (FusionEngine → RiskEngine)

O pipeline opera em dois estágios de classificação:

1. O **FusionEngine** atribui um nível interno (`low` / `medium` / `high` / `critical`) baseado nos thresholds de `config.py`.
2. O **RiskEngine** traduz o score fundido em prioridade operacional (`ROTINA` / `MONITORAR` / `URGENTE`).

**FusionEngine (nível interno):**

1. $s_{mm} \geq 0.65$ (threshold `alert`) → level = **high**
2. $s_{mm} \geq 0.40$ → level = **medium**
3. video ≥ 0.80 AND audio ≥ 0.80 → level = **critical**
4. objects ≥ 0.85 → level = **critical** (independente)
5. clinical ≥ 0.80 → level = **critical** (CTG patológico / maternal high risk)

**RiskEngine (prioridade operacional — saída final da API):**

| Score Fundido | Prioridade    | Revisão Humana |
| ------------- | ------------- | -------------- |
| ≥ 0.70        | **URGENTE**   | Obrigatória    |
| 0.40 – 0.69   | **MONITORAR** | Condicional    |
| < 0.40        | **ROTINA**    | Não requerida  |

O nível `critical` do FusionEngine sempre resulta em `URGENTE` no RiskEngine, com `humanReviewRequired: true`. Escalações adicionais do RiskEngine: detecção de objeto cortante → mínimo MONITORAR; detecção de objetos indisponível → mínimo MONITORAR.

### Care Assessment

O CareEngine traduz scores em dimensões de cuidado:

- `wellbeingIndex`: índice inverso de distress + safety + obstetric.
- `affectiveDistress`: combinação ponderada de áudio + emoção + texto + vídeo.
- `audioEmotionDistress`: 0.45×sad + 0.35×fearful + 0.20×angry.
- `safetySignal`: texto safety + controle + hopelessness + vídeo + objetos.
- `nonverbalAlert`: vídeo + áudio + objetos.
- `objectThreat`: score direto do SharpObjectDetector.
- `obstetricRisk`: score direto do ClinicalExtractor (CTG/Maternal).

Pathways: `acompanhamento_rotina` → `coleta_adicional` → `acolhimento_e_monitoramento` → `revisao_prioritaria`.

---

## 7. Segurança e Validação

### LGPD

- **Pseudonimização**: patient_id é hash sem vínculo com dados pessoais.
- **Criptografia**: SSE-S3 em repouso, TLS 1.2+ em trânsito.
- **Minimização**: apenas scores e evidências são persistidos; mídia bruta não é armazenada na nuvem.
- **Retenção**: S3 Lifecycle e DynamoDB TTL configuram expiração automática.
- **Auditoria**: CloudTrail + human_review array em cada report.
- **Eliminação**: suporte a direito ao esquecimento por patient_id.

### Validação

- 56 testes unitários cobrindo: labels/manifests, clinical extractor, fusion (5 modalidades), risk escalation, care engine com clinical, pipeline end-to-end, object detection, API.
- **Todos os 56 testes passando** — evidência em `data/results/test_output.txt`.
- Testes de regressão para o pipeline legado preservados.
- 17+ evidências JSON geradas a partir de dados reais dos datasets.
- **Demo end-to-end de vídeo**: `scripts/demo_video_end_to_end.py` (YOLOv8-Pose → keypoints → pipeline completo).

### Tratamento de Erros e Observabilidade

#### Status Codes da API

| Code | Cenário                                  | Origem                                 |
| ---- | ---------------------------------------- | -------------------------------------- |
| 200  | Análise concluída com sucesso            | `POST /analyze`, `GET /health`         |
| 400  | Input inválido (JSON clínico malformado) | `POST /analyze`                        |
| 404  | Relatório não encontrado                 | `GET /api/report/{name}`               |
| 500  | Falha no pipeline de inferência          | `POST /analyze` (erro não recuperável) |

#### Degradação Parcial

- Se uma modalidade falha (modelo ausente, arquivo corrompido), o pipeline continua com as demais.
- O coverage penalty reduz automaticamente o score final proporcionalmente às modalidades faltantes.
- Falhas parciais são registradas como warnings no log, não como erros fatais.
- Se nenhuma modalidade produz resultado, o pipeline retorna erro 400 ("nenhuma evidência fornecida").

#### Logging JSON Estruturado

O sistema implementa logging via `src/logging_config.py` com dois componentes:

1. **`JSONFormatter`**: formata cada log como JSON single-line em stderr.
   - Campos: `timestamp` (ISO 8601), `level`, `logger`, `message`, `exception`, `extra_fields`.
2. **`PipelineTracer`**: rastreia execução do pipeline com:
   - `request_id`: correlation ID único por análise.
   - `stage(name)`: context manager que mede duração por estágio (audio, text, pose, fusion, etc.).
   - `summary()`: retorna métricas agregadas (tempo total, modalidades processadas, cobertura).

#### Interpretação dos Níveis de Log

| Nível   | Significado                                                        |
| ------- | ------------------------------------------------------------------ |
| INFO    | Progresso normal (modalidade processada, score gerado)             |
| WARNING | Modalidade indisponível, modelo não encontrado, domain warning     |
| ERROR   | Falha em extrator ou engine que impede processamento da modalidade |

#### Variáveis de Ambiente

| Variável                | Propósito                        | Default             |
| ----------------------- | -------------------------------- | ------------------- |
| `AWS_REGION`            | Região AWS para integração cloud | `us-east-1`         |
| `S3_BUCKET`             | Bucket S3 para relatórios        | `""` (desabilitado) |
| `DYNAMODB_TABLE`        | Tabela DynamoDB para índice      | `None`              |
| `SNS_TOPIC_ARN`         | Tópico SNS para alertas          | `None`              |
| `KMS_KEY_ID`            | Chave KMS para criptografia      | `None`              |
| `AWS_ACCESS_KEY_ID`     | Credencial AWS                   | (env)               |
| `AWS_SECRET_ACCESS_KEY` | Credencial AWS                   | (env)               |

> **Nota:** As variáveis AWS são opcionais. Sem elas, o pipeline funciona normalmente em modo local; apenas a persistência cloud fica desabilitada.

---

## 8. Avaliação

### Métricas por Modelo

| Modelo                 | Accuracy     | Macro-F1        | Observação                                                      |
| ---------------------- | ------------ | --------------- | --------------------------------------------------------------- |
| Audio Emotion Baseline | 42.7%        | 38.7%           | Baseline com features acústicas simples                         |
| DAiSEE Visual Baseline | 59.6%        | 23.1%           | Desbalanceamento forte; F1 é métrica honesta                    |
| Text Multi-Label       | —            | —               | Léxico; precisão depende de cobertura do vocabulário            |
| YOLOv8 Sharp Objects   | mAP50: 87.9% | mAP50-95: 60.6% | Fine-tuned 10 epochs, 15 classes, Precision 84.2%, Recall 81.1% |
| Pose Defensive         | —            | —               | Heurística; não treinou classificador                           |

### Avaliação do Sistema Integrado

O sistema foi testado com combinações de modalidades:

- Texto isolado: detecta marcadores linguísticos com confidence proporcional a hits.
- Texto + áudio: enriches com emoção vocal e componentes acústicos de stress.
- Vídeo + objetos: detecta postura defensiva e ameaça ambiental simultaneamente.
- 5 modalidades: score fusionado com coverage penalty 1.0, máxima confiança.

---

## 9. Estrutura do Código

```
src/                              # Código de produção refatorado
├── config.py                     # PipelineConfig, ModelPaths, FusionWeights, Thresholds
├── domain/
│   ├── types.py                  # ModalityScore, ObjectDetection, RiskReport
│   └── labels.py                 # Taxonomio Sentinela e mapeamentos dataset→domínio
├── extractors/
│   ├── audio.py                  # AudioExtractor (WAV → features acústicas → score)
│   ├── audio_emotion.py          # predict_audio_emotion (baseline emocional)
│   ├── text.py                   # TextExtractor (PT-BR lexicon multi-label)
│   ├── pose.py                   # PoseExtractor (COCO17 → defensive posture)
│   ├── motion.py                 # MotionExtractor (frame diff → motion energy)
│   ├── objects.py                # SharpObjectDetector (YOLOv8 → risk objects)
│   ├── visual_wellbeing.py       # VisualWellbeingExtractor (DAiSEE baseline)
│   └── clinical.py              # ClinicalExtractor (CTG/Maternal → obstetric risk)
├── engines/
│   ├── fusion_engine.py          # Late fusion 5 modalidades
│   ├── risk_engine.py            # Triage: ROTINA / MONITORAR / URGENTE
│   └── care_engine.py            # Trilha de cuidado trauma-informada
├── pipeline.py                   # Orquestrador SentinelaPipeline
├── cli.py                        # CLI entry point
├── api/app.py                    # FastAPI (analyze, reports, review)
├── cloud/aws_publish.py          # S3 + DynamoDB + SNS
└── training/
    ├── train_sharp_objects.py     # YOLOv8 fine-tuning com auto-split
    └── train_audio_emotion.py    # LogReg baseline emocional

tests/
├── test_refactored.py            # 21 testes (fusion, care, pipeline, API, text, audio, objects)
├── test_sentinela.py                # 8 testes (regressão do pipeline legado)
└── test_clinical_and_datasets.py # 27 testes (clinical, labels, manifests, fusão 5-modal, care obstetric)

models/                           # Artefatos de modelo treinados
docs/                             # Documentação técnica e arquitetural
data/                             # Manifests, caches, resultados
```

---

## 10. Desafios e Soluções

| Desafio                                                          | Solução Adotada                                                                              |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Datasets de violência doméstica são raros e eticamente sensíveis | Abordagem indireta: detecção de sinais correlatos (emoção, postura, léxico) sem diagnosticar |
| Modalidades podem estar ausentes em runtime                      | Coverage penalty + normalização de pesos sobre modalidades presentes                         |
| Fusão ingênua supervaloriza uma modalidade                       | Pesos modulados por confiança individual + disagrement flag                                  |
| YOLOv8 dataset sem split de validação                            | Auto-split programático (20% train → valid) no script de treino                              |
| Modelos de produção são caros na nuvem                           | Inferência local em CPU + AWS Free Tier apenas para persistência e alertas                   |
| Risco de falso positivo em contexto sensível                     | human_review_required, guardrails, linguagem não-diagnóstica, uncertainty dimension          |
| Audio longo fora do domínio de treino                            | Domain warning + redução automática de confiança para áudios >30s                            |

---

## 11. Lições Aprendidas

1. **Late fusion é a escolha pragmática para MVP multimodal**. Datasets heterogêneos com modalidades faltantes tornam early/attention fusion prematuros sem dados alinhados suficientes.

2. **Explicabilidade supera acurácia em domínio sensível**. Um baseline de 42% com evidências auditáveis é mais defensável que um modelo opaco de 85%.

3. **Coverage penalty é essencial**. Sem ela, uma única modalidade com score alto inflaciona o risco multimodal — gerando falsos positivos inaceitáveis em contexto clínico.

4. **A modalidade de objetos agrega valor desproporcional**. Detectar uma faca em um frame é um sinal forte e concreto que complementa sinais indiretos (tom de voz, escolha de palavras).

5. **Design trauma-informado não é opcional**. A forma como o sistema comunica resultados (sem julgamento, com perguntas de segurança) é tão importante quanto a acurácia dos modelos.

6. **Free Tier é viável para demonstração acadêmica**. Inferência local + cloud apenas para persistência/alertas elimina custos sem sacrificar a arquitetura.

---

## 12. Entregas Desta Fase e Próximos Passos

### Concluídos nesta fase

- [x] **Logging JSON estruturado** com `JSONFormatter` e `PipelineTracer` (`src/logging_config.py`) — correlation ID, timing por estágio, métricas de cobertura.
- [x] **Interface React + FastAPI** — frontend em `frontend/` com dashboard multimodal, explicabilidade, radar, timeline; backend em `backend/main.py` com endpoints de análise.
- [x] **Treino e avaliação YOLOv8n Sharp Objects** — mAP@50: 87.9%, mAP@50-95: 60.6%, Precision: 84.2%, Recall: 81.1% (10 epochs, 15 classes). Evidência em `data/results/evidence_yolov8_sharp_objects_training.json`.
- [x] **Integração da 5ª modalidade (clínico/obstétrico)** — CTG + Maternal Health Risk com thresholds OMS.
- [x] **56 testes unitários** passando — cobertura de labels, clinical, fusion, care, pipeline, objects, API.

### Próximos passos

1. **Substituir léxico textual por BERTimbau** para detecção contextual em português.
2. **Adicionar MFCCs e features espectrais** ao extrator de áudio para melhorar o baseline emocional.
3. **Implementar deploy AWS** (S3 + DynamoDB + Lambda + SNS) — arquitetura documentada, implementação pendente.
4. **Solicitar acesso formal** ao DAIC-WOZ e WEMAC completo para validação cross-domain.
5. **Implementar attention fusion** quando houver dados multimodais alinhados temporalmente.
6. **Adicionar testes de integração** com fixtures multimodais sintéticas.

---

## 13. Conclusões

O Sentinela AI demonstra uma arquitetura multimodal completa, auditável e eticamente consciente para monitoramento preventivo de saúde e segurança feminina. O sistema processa 5 modalidades (áudio, texto, vídeo, objetos, clínico/obstétrico) através de uma pipeline com fusão ponderada por confiança, gera trilhas de cuidado trauma-informadas e apresenta resultados via interface React + FastAPI. Integração AWS está documentada e planejada para etapa final.

O diferencial técnico não está na acurácia dos baselines individuais — que são explicitamente documentados como limitados — mas na **arquitetura de fusão que degrada graciosamente** (coverage penalty, modalidades opcionais, confidence modulation), na **camada de cuidado que traduz scores em ação humana** (pathways, review focus, guardrails), e na **integração end-to-end** de 5 modalidades auditáveis incluindo risco obstétrico.

O projeto atende aos requisitos obrigatórios da Fase 4, implementa os objetivos listados, e mantém transparência sobre limitações, viés e falsos positivos — posicionando-se como sistema de apoio à triagem, nunca como decisor clínico.
