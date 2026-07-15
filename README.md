# Sentinela AI

**Sistema Multimodal de Apoio a Seguranca Publica e Protecao Integral da Mulher**

> _[English version below](#english)_

O Sentinela AI combina relatos, audio, video, imagem e dados clinicos para analise multimodal de sinais de risco e vulnerabilidade, apoiando a seguranca publica e a protecao integral da mulher. Gera relatorios auditaveis com trilhas de cuidado trauma-informadas, projetado como ferramenta de apoio a triagem e revisao humana — nunca como sistema diagnostico ou decisorio automatizado.

---

## Quick Start

```bash
# 1. Clonar e instalar dependencias
git clone <url-do-repositorio>
cd "Tech Challenge IADT - Fase 4"
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Windows
pip install -r requirements.txt       # Instala TODAS as dependencias (ML, API, etc.)

# 2. Iniciar o backend (FastAPI)
cd backend
uvicorn main:app --reload --port 8000

# 3. Iniciar o frontend (React) — em outro terminal
cd frontend
npm install
npm run dev

# 4. Acessar no navegador
# http://localhost:5173
```

**Testes:**

```bash
python -m pytest tests/ -v
```

**Demo rapido (Streamlit):**

```bash
streamlit run app_demo.py
```

---

## Problema

A violencia domestica contra mulheres frequentemente se manifesta por sinais indiretos: hesitacao vocal, alteracao de tom, posturas corporais defensivas, presenca de objetos cortantes no ambiente e marcadores linguisticos de medo, controle ou isolamento. Esses sinais aparecem em multiplas modalidades e raramente em uma unica fonte de dados.

Equipes clinicas precisam de ferramentas que sintetizem sinais heterogeneos em indicadores de triagem acionaveis — sem fazer afirmacoes diagnosticas, sem substituir o julgamento humano e sem expor dados sensiveis.

### Por Que Este Projeto Importa

- Sistemas de modalidade unica perdem padroes cross-modais.
- Profissionais clinicos precisam de suporte a decisao estruturado e auditavel.
- Restricoes eticas (LGPD, cuidado trauma-informado) exigem design intencional desde o inicio.
- Falta de sistemas baseline multimodais abertos e reproduziveis neste dominio.

### Diferenciais

- **Fusao tardia de 5 modalidades** (texto, audio, video, objetos, clinico) com normalizacao ponderada por confianca e penalidade de cobertura.
- **Camada de cuidado trauma-informado** traduzindo scores em trilhas acionaveis (nao diagnosticos).
- **Degradacao graciosa** — funciona com qualquer subconjunto de modalidades, ajustando confianca.
- **Honestidade academica** — todas as limitacoes, vieses e restricoes dos baselines sao documentados.
- **Interface React + FastAPI** — frontend moderno com dashboard interativo e backend de inferencia.
- **Arquitetura Azure para Cognitive Services e alerta clinico**
- **Logging estruturado** — rastreamento JSON por pipeline com correlation ID e metricas de tempo.

---

## Arquitetura

```
                          +--------------------+
                          |  Fontes de Entrada |
                          |  (audio, texto,    |
                          |   video, imagens)  |
                          +--------+-----------+
                                   |
                    +--------------+--------------+
                    |              |              |              |
              +-----+----+  +----+-----+  +-----+----+  +------+-----+
              |  Audio   |  |   Texto  |  |  Video   |  |  Objetos   |
              | Extrator |  | Extrator |  | Extrator |  |  Detector  |
              +-----+----+  +----+-----+  +-----+----+  +------+-----+
                    |              |              |              |
                    |         ModalityScore       |              |
                    +--------------+--------------+--------------+
                                   |
                          +--------+---------+
                          |  Motor de Fusao  |
                          |  (fusao tardia,  |
                          |   ponderada por  |
                          |   confianca)     |
                          +--------+---------+
                                   |
                    +--------------+--------------+
                    |                             |
              +-----+------+            +--------+--------+
              | Motor de   |            | Motor de        |
              | Risco      |            | Cuidado         |
              | (triagem)  |            | (trauma-        |
              +-----+------+            |  informado)     |
                    |                    +--------+--------+
                    |                             |
                    +-----------------------------+
                                   |
                          +--------+---------+
                          |   RiskReport     |
                          |   (saida JSON)   |
                          +------------------+
```

### Modalidades

| Modalidade | Entrada                                | Extratores                                                                      | Sinais                                                                             |
| ---------- | -------------------------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Audio      | Arquivos WAV                           | Features acusticas (RMS, ZCR, silencio, clipping) + baseline emocional (LogReg) | Estresse vocal, distress emocional, padroes de pausa                               |
| Texto      | Transcricoes (PT-BR)                   | NLP multi-label baseado em lexico com deteccao de negacao                       | Preocupacao com seguranca, coercao, isolamento, desesperanca, distress psicologico |
| Video      | Pose JSON / frames / arquivos de video | YOLOv8-Pose (postura defensiva), energia de movimento, bem-estar visual DAiSEE  | Postura defensiva, agitacao, tedio/confusao/frustracao                             |
| Objetos    | Imagens / frames de video              | YOLOv8n pre-treinado (COCO) com fallback + fine-tuning disponivel               | Ameaca ambiental (facas, tesouras, etc.)                                           |
| Clinico    | Dados estruturados (CSV/JSON)          | Extrator clinico baseado em regras (OMS) + classificacao CTG/Maternal           | Risco obstetrico, risco fetal, sinais vitais anormais                              |

### Estrategia de Fusao

Fusao tardia com normalizacao ponderada por confianca:

$$s_{mm} = \sum_{m} w_m^{norm} \cdot s_m \cdot \text{coverage\\_penalty}(n)$$

Os pesos sao modulados pela confianca por modalidade, e uma penalidade de cobertura reduz o score fundido quando menos modalidades estao disponiveis (1 mod: 0.88, 2: 0.94, 3: 0.97, 4: 0.99, 5: 1.0).

Pesos base: video=0.25, audio=0.20, text=0.20, objects=0.15, clinical=0.20.

---

## Funcionalidades

- **Deteccao de Risco**: Triagem multi-nivel (ROTINA / MONITORAR / URGENTE) com flags de anomalia.
- **Analise de Audio**: Extracao de features acusticas + baseline emocional (6 emocoes de RAVDESS).
- **Analise de Texto**: Deteccao de sinais multi-label baseada em lexico portugues com tratamento de negacao.
- **Analise de Postura**: Heuristica de postura defensiva COCO17 com agregacao temporal.
- **Analise de Movimento**: Diferenca pixel-a-pixel entre frames com calibracao configuravel.
- **Bem-Estar Visual**: Predicao DAiSEE de tedio/engajamento/confusao/frustracao.
- **Deteccao de Objetos**: YOLOv8n pre-treinado (COCO) com fallback automatico; fine-tuning disponivel para 15 classes.
- **Motor de Fusao**: Fusao tardia de 5 modalidades com penalidade de cobertura e modulacao de confianca.
- **Motor de Cuidado**: Avaliacao trauma-informada com 9 dimensoes e 4 trilhas de cuidado.
- **Risco Obstetrico**: Modalidade clinica com CTG e Maternal Health Risk (WHO thresholds).
- **Revisao Humana**: Trilha de auditoria para revisao clinica (PENDING/CONFIRMED/DISMISSED/ESCALATED).
- **Integracao Cloud**: Azure Speech-to-Text, Azure AI Language, Blob Storage e Service Bus por chamada REST
- **Interface React**: Dashboard com visualizacao multimodal, explicabilidade, timeline e radar.
- **Observabilidade**: Logging JSON estruturado com correlation ID e metricas por estagio.

---

## Stack Tecnica

| Categoria  | Tecnologias                                                  |
| ---------- | ------------------------------------------------------------ |
| Linguagem  | Python 3.10+                                                 |
| ML / Visao | Ultralytics YOLOv8, scikit-learn, OpenCV, NumPy, Pandas      |
| Audio      | OpenAI Whisper (transcricao), extracao de features acusticas |
| API        | FastAPI, Uvicorn, Pydantic                                   |
| Frontend   | React 18, TypeScript, Vite, Tailwind CSS, Recharts           |
| Cloud      | Azure AI Services, Blob Storage, Service Bus e Key Vault |
| Dados      | yt-dlp, joblib, PyYAML                                       |
| Testes     | unittest (56 testes)                                         |

---

## Instalacao

### Pre-requisitos

- Python 3.10 ou superior
- `ffmpeg` no PATH (para processamento de audio)
- Git

### Setup

```bash
git clone <url-do-repositorio>
cd "Tech Challenge IADT - Fase 4"

python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### Variaveis de Ambiente (opcional, para integracao Azure)

```bash
export AZURE_REGION=brazilsouth
export AZURE_COGNITIVE_ENDPOINT=https://<recurso>.cognitiveservices.azure.com/
export AZURE_COGNITIVE_KEY=<chave>
export AZURE_STORAGE_ACCOUNT=<conta>
export AZURE_STORAGE_CONTAINER=sentinela-reports
export AZURE_SERVICE_BUS_NAMESPACE=<namespace>
export AZURE_SERVICE_BUS_QUEUE=clinical-alerts
export AZURE_SERVICE_BUS_CONNECTION_STRING="<connection-string-da-regra-sentinela-alert-sender>"
export AZURE_KEY_VAULT_NAME=<key-vault>
```

Com `AZURE_COGNITIVE_ENDPOINT` + `AZURE_COGNITIVE_KEY`, o pipeline chama Azure AI Speech para transcrever audio e Azure AI Language para sentimento e key phrases. Com `AZURE_SERVICE_BUS_CONNECTION_STRING`, alertas URGENTE/revisao humana sao enviados para a fila `clinical-alerts`.

---

## Uso

### Modos de Execucao

| Modo           | Comando                                      | Interface              | Quando usar                               |
| -------------- | -------------------------------------------- | ---------------------- | ----------------------------------------- |
| Frontend + API | `cd backend && uvicorn main:app --port 8000` | React (localhost:5173) | Demo principal, apresentacao              |
| API Completa   | `uvicorn src.api.app:app --port 8000`        | Dashboard web embutido | Desenvolvimento, acesso a todos endpoints |
| Demo rapido    | `streamlit run app_demo.py`                  | Streamlit              | Teste rapido sem frontend                 |
| CLI            | `python -m src.cli --transcript ...`         | Terminal               | Automacao, scripts, CI/CD                 |

> **Nota:** `backend/main.py` e o backend otimizado para o frontend React (2 endpoints: `GET /health`, `POST /analyze`). `src/api/app.py` e a API completa com endpoints adicionais de relatorios e revisao humana. Ambos importam o mesmo `SentinelaPipeline` de `src/`.

### Interface Oficial (React + FastAPI)

A interface principal e o frontend React em `frontend/`, conectado ao backend FastAPI em `backend/`.

**Pre-requisito:** instalar as dependencias da raiz do projeto (`pip install -r requirements.txt`) antes de iniciar o backend.

**1. Iniciar o backend:**

```bash
cd backend
uvicorn main:app --reload --port 8000
```

**2. Iniciar o frontend:**

```bash
cd frontend
npm install
npm run dev
```

**3. Acessar no navegador:**

```
http://localhost:5173
```

O dashboard inclui:

1. **Painel de Risco** — score de fusao, nivel de triagem, confianca, revisao humana.
2. **Visualizacao Multimodal** — barras horizontais e grafico radar com todas as dimensoes.
3. **Explicabilidade** — ranking de sinais com contribuicao ponderada por modalidade.
4. **Timeline** — eventos de analise ao longo do pipeline.
5. **Recomendacao de Cuidado** — trilha trauma-informada com guardrails eticos.
6. **Trace do Pipeline** — visao de engenharia com tempos por estagio.
7. **JSON Completo** — relatorio para auditoria.

O frontend aceita 5 tipos de entrada:

- **Relato/transcricao** (texto livre)
- **Audio** (WAV)
- **Video** (MP4, AVI, MOV)
- **Imagem** (JPG, PNG)
- **Dados clinicos** (formulario com idade, PA, glicose, temperatura, FC)

### Demo Legado (Streamlit)

O prototypo Streamlit em `app_demo.py` ainda esta disponivel para testes rapidos:

```bash
streamlit run app_demo.py
```

> **Nota:** Use o frontend React para demonstracao.

### CLI

```bash
# Analise somente texto
python -m src.cli --transcript data/transcripts/amostra.txt

# Texto + audio
python -m src.cli \
  --transcript data/transcripts/amostra.txt \
  --audio-wav data/audio/amostra.wav

# Analise de postura por video
python -m src.cli --pose-json data/pose/pose_keypoints.json

# Multimodal completo (todas as entradas)
python -m src.cli \
  --transcript data/transcripts/amostra.txt \
  --audio-wav data/audio/amostra.wav \
  --pose-json data/pose/pose_keypoints.json \
  --image-for-objects imagem_teste.jpg \
  --out data/results/relatorio_completo.json
```

### API

A API completa (com endpoints de relatorios e revisao humana) esta em `src/api/app.py`:

```bash
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000
```

Endpoints (`src/api/app.py`):

| Metodo | Caminho                     | Descricao                      |
| ------ | --------------------------- | ------------------------------ |
| GET    | `/`                         | Dashboard web                  |
| GET    | `/api/health`               | Health check                   |
| POST   | `/api/analyze`              | Executar analise multimodal    |
| GET    | `/api/reports`              | Listar relatorios salvos       |
| GET    | `/api/report/{name}`        | Recuperar relatorio especifico |
| POST   | `/api/report/{name}/review` | Registrar revisao humana       |

Endpoints (`backend/main.py` — usado pelo frontend React):

| Metodo | Caminho    | Descricao                   |
| ------ | ---------- | --------------------------- |
| GET    | `/health`  | Health check                |
| POST   | `/analyze` | Executar analise multimodal |

### Tratamento de Erros da API

| Status | Cenario                                          |
| ------ | ------------------------------------------------ |
| 200    | Analise concluida com sucesso                    |
| 400    | Input invalido ou nenhuma evidencia fornecida    |
| 404    | Relatorio nao encontrado                         |
| 500    | Falha no pipeline (modelo ausente, erro interno) |

### Saida Esperada

```json
{
  "multimodal_score_0_1": 0.482,
  "level": "medium",
  "weights": { "video": 0.0, "audio": 0.0, "text": 1.0, "objects": 0.0 },
  "priority": {
    "riskLevel": "MONITORAR",
    "confidence": 0.867,
    "humanReviewRequired": false
  },
  "care_assessment": {
    "carePathway": "acolhimento_e_monitoramento",
    "dimensions": {
      "wellbeingIndex": 0.712,
      "affectiveDistress": 0.263,
      "safetySignal": 0.251
    }
  }
}
```

---

## Evidencias de Funcionamento

Exemplos reprodutiveis pelo pipeline. Para gerar os JSON localmente, execute `python scripts/generate_evidence_v2.py`; os arquivos serao gravados em `data/results/`.

| Cenario                                  | Descricao                                      | Score     | Priority  | Care Pathway                |
| ---------------------------------------- | ---------------------------------------------- | --------- | --------- | --------------------------- |
| Maternal high risk                       | Maternal Health: high risk (SBP=140, BS=13)    | 0.722     | URGENTE   | revisao_prioritaria         |
| Maternal low risk                        | Maternal Health: low risk                      | 0.106     | ROTINA    | acompanhamento_rotina       |
| CTG pathological                         | CTG pathological (NSP=3, severe decelerations) | 0.748     | URGENTE   | revisao_prioritaria         |
| CTG normal                               | CTG normal (NSP=1)                             | 0.088     | ROTINA    | acompanhamento_rotina       |
| Texto psicologico                        | Texto: medo, ansiedade, insonia, isolamento    | 0.441     | MONITORAR | acompanhamento_rotina       |
| Texto + clinical mid risk                | Multimodal: texto distress + clinical mid risk | 0.397     | ROTINA    | acolhimento_e_monitoramento |
| EATD-Corpus audio                        | EATD-Corpus audio (SDS=82.5, depression)       | gerado    | —         | —                           |
| RAVDESS fearful audio                    | RAVDESS audio (fearful emotion)                | gerado    | —         | —                           |
| Objeto fork                              | Fork detectado via COCO YOLOv8 (conf 0.891)    | gerado    | MONITORAR | —                           |

Para regenerar: `python scripts/generate_evidence_v2.py`

### Modelos Pre-Treinados

O projeto usa modelos pre-treinados (autorizado pelo professor) com fallback hierarquico:

- **YOLOv8n COCO**: detecta knife, scissors, fork como proxy de objetos perigosos.
- **YOLOv8n-Pose COCO17**: extrai keypoints para heuristica de postura defensiva.
- **LogReg RAVDESS**: baseline emocional treinado localmente.
- **RandomForest DAiSEE**: baseline de bem-estar visual treinado localmente.

Ver `TECHNICAL_REPORT.md` secao 4.1 para justificativa tecnica completa.

---

## Estrutura do Projeto

```
app_demo.py                     # Dashboard Streamlit (demo interativo)
src/
  config.py                     # Configuracao centralizada (dataclasses)
  pipeline.py                   # Orquestrador (compoe extratores + motores)
  logging_config.py             # Logging JSON estruturado + PipelineTracer
  cli.py                        # Ponto de entrada CLI
  domain/
    types.py                    # Value objects (ModalityScore, RiskReport, ObjectDetection)
    labels.py                   # Taxonomio Sentinela e mapeamentos dataset->dominio
  extractors/
    audio.py                    # WAV -> features acusticas -> ModalityScore
    audio_emotion.py            # Predicao baseline emocional (LogReg)
    text.py                     # NLP multi-label lexico PT-BR
    pose.py                     # Keypoints COCO17 -> postura defensiva
    motion.py                   # Diferenca entre frames -> energia de movimento
    objects.py                  # Deteccao de objetos cortantes YOLOv8
    visual_wellbeing.py         # Predicao de bem-estar visual DAiSEE
    clinical.py                 # Risco obstetrico/maternal (CTG + sinais vitais)
  engines/
    fusion_engine.py            # Fusao tardia (5 modalidades)
    risk_engine.py              # Triagem: ROTINA / MONITORAR / URGENTE
    care_engine.py              # Avaliacao trauma-informada de cuidado
  api/
    app.py                      # Aplicacao FastAPI
    static/                     # Dashboard web (HTML/JS/CSS)
  cloud/
    azure_integration.py        # Envelope Azure AI Services + Blob + Service Bus
  training/
    train_audio_emotion.py      # Treino do baseline de emocao por audio
    train_sharp_objects.py      # Fine-tuning YOLOv8 com auto-split
tests/
  test_sentinela.py                # Testes de integracao (8 testes)
  test_refactored.py            # Testes unitarios de todos os componentes (21 testes)
  test_clinical_and_datasets.py # Testes clinico, labels, manifests, fusao (27 testes)
scripts/
  generate_evidence_v2.py       # Gera evidencias completas (clinico, audio, texto, objetos)
  build_all_manifests.py        # Constroi manifests de todos os datasets
  generate_evidence.py          # Gera resultados de evidencia para avaliacao
  prepare_audio_datasets.py     # Prepara manifests de RAVDESS/CREMA-D
  prepare_video_datasets.py     # Prepara manifests de DAiSEE/XD-Violence/UCF-Crime
  build_emotion_manifest.py     # Constroi manifest combinado de emocao
  train_daisee_visual_baseline.py # Treina baseline visual DAiSEE
  render_case_summary.py        # Renderiza sumario de caso
  render_html_report.py         # Renderiza relatorio HTML
data/                           # Manifestos, caches, resultados
infra/azure/                    # Infraestrutura Azure em Bicep
```

---

## Datasets

| Dataset                                                                              | Link Oficial                                                                   | Pasta Local                       | Modalidade    | Uso no Projeto                                              | Status                                                            | Obs. Eticas/Licenca                 |
| ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ | --------------------------------- | ------------- | ----------------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------- |
| [RAVDESS](https://smartlaboratory.org/resources/speech-song-database-ravdess/)       | [Zenodo](https://zenodo.org/record/1188976)                                    | `The Ryerson Audio-Visual.../`    | Audio         | Baseline emocional (medo, tristeza, raiva, calma, neutro)   | ✅ Baixado, manifest gerado (1012 entries), usado em teste        | CC BY-NC-SA 4.0; fala atuada        |
| [EATD-Corpus](https://github.com/speechandlanguageprocessing/ICASSP2022-Depression)  | [GitHub](https://github.com/speechandlanguageprocessing/ICASSP2022-Depression) | `EATD-Corpus - Automatic.../`     | Audio + Texto | Depressao/distress psicologico (SDS score)                  | ✅ Baixado, manifest gerado (972 entries), usado em teste         | Pesquisa academica; texto em chines |
| [DAiSEE](https://people.iith.ac.in/vineethnb/resources/daisee/)                      | [IIT-H](https://people.iith.ac.in/vineethnb/resources/daisee/)                 | `DAiSEE/DAiSEE/`                  | Video         | Bem-estar visual (tedio, engajamento, confusao, frustracao) | ✅ Baixado, manifest gerado (17496 entries), baseline treinado    | CC BY 4.0; contexto educacional     |
| [Cardiotocography](https://archive.ics.uci.edu/dataset/193/cardiotocography)         | [UCI ML](https://archive.ics.uci.edu/dataset/193/cardiotocography)             | `cardiotocography/`               | Clinico       | Risco fetal (Normal/Suspect/Pathological) via CTG           | ✅ Baixado, manifest gerado (2126 entries), integrado no pipeline | CC BY 4.0; dados anonimizados       |
| [Maternal Health Risk](https://archive.ics.uci.edu/dataset/863/maternal+health+risk) | [UCI ML](https://archive.ics.uci.edu/dataset/863/maternal+health+risk)         | `maternal+health+risk/`           | Clinico       | Risco obstetrico (low/mid/high risk) via sinais vitais      | ✅ Baixado, manifest gerado (1014 entries), integrado no pipeline | CC BY 4.0; dados anonimizados       |
| [XD-Violence](https://roc-ng.github.io/XD-Violence/)                                 | [GitHub](https://roc-ng.github.io/XD-Violence/)                                | `video/xd-violance/`              | Video         | Proxy de anomalia visual/safety (NAO e dado clinico)        | ✅ Exemplos baixados (16 videos), manifest gerado                 | Pesquisa academica; apenas proxy    |
| [Sharp Objects (Roboflow)](https://universe.roboflow.com/)                           | Roboflow                                                                       | `Sharp Objects Detection.yolov8/` | Imagem        | Fine-tuning YOLOv8 (15 classes de objetos cortantes)        | ✅ Baixado, usado com COCO fallback                               | Roboflow terms; dados publicos      |

### Consideracoes Eticas

- Todos os datasets sao publicamente disponiveis ou usados sob termos academicos.
- Nenhuma informacao pessoal identificavel (PII) e usada em treino ou inferencia.
- O sistema adota uma **abordagem indireta**: nao diagnostica violencia domestica. Identifica sinais correlacionados e encaminha para revisao humana.
- Modelos de emocao por audio sao treinados em fala atuada, o que limita validade ecologica. Isso e documentado explicitamente e refletido nos scores de confianca.

---

## Estrategia de Modelos

### Baselines (intencionalmente simples e explicaveis)

| Modelo                    | Tipo                | Acuracia     | Macro-F1        | Justificativa                                                               |
| ------------------------- | ------------------- | ------------ | --------------- | --------------------------------------------------------------------------- |
| Emocao por Audio          | Regressao Logistica | 42,7%        | 38,7%           | Simples, explicavel; apenas features acusticas                              |
| Bem-Estar Visual (DAiSEE) | Random Forest       | 59,6%        | 23,1%           | Baseline interpretavel; F1 reflete desbalanceamento de classes honestamente |
| Sinais de Texto           | Baseado em lexico   | N/A          | N/A             | Baseado em regras; precisao depende de cobertura do vocabulario             |
| Objetos Cortantes         | YOLOv8n             | mAP50: 87.9% | mAP50-95: 60.6% | Fine-tuned 10 epochs, 15 classes, Precision 84.2%, Recall 81.1%             |
| Postura Defensiva         | Heuristica          | N/A          | N/A             | Baseada em geometria; sem classificador treinado                            |

### Por Que Baselines, Nao Deep Learning?

1. **Explicabilidade sobre acuracia** em um dominio clinico sensivel.
2. **Reprodutibilidade** sem requisitos de GPU.
3. **Auditabilidade** — cada score pode ser rastreado ate features especificas.
4. **Documentacao honesta** — reportamos o que os modelos podem e nao podem fazer.

---

## Testes

```bash
python -m unittest discover -s tests -v
```

56 testes cobrindo:

- **Labels & Manifests**: Taxonomio Sentinela, mapeamentos RAVDESS/EATD/CTG/Maternal, leitura de manifests
- **Clinical Extractor**: CTG (Normal/Suspect/Pathological), Maternal Risk (low/mid/high), sinais vitais
- **Fusion (5 modalidades)**: Fusao clinica isolada, clinica + texto, 5 modalidades com cobertura total
- **Care Engine**: Trilha obstetrica, dimensao obstetricRisk, review focus clinico
- **Pipeline Integration**: Clinical data through pipeline, text + clinical multimodal
- **Object Detection**: Deteccao, fallback COCO, escalacao de risco, revisao humana
- **Text/Audio/Video**: Sinais de texto, fusao, penalidade de cobertura
- **API**: Health check, endpoints

---

## Arquitetura Cloud (Azure)

| Servico Azure | Funcao |
| --- | --- |
| Azure AI Services | Speech-to-Text para audio e Language para sentimento/key phrases |
| Azure Blob Storage | Armazenamento criptografado de relatorios e envelopes |
| Azure Service Bus | Fila de alertas clinicos para equipe medica |
| Azure Key Vault | Segredos e chaves de integracao |
| Log Analytics + Application Insights | Observabilidade do pipeline e da API |

> **Status:** Template Bicep disponivel em `infra/azure/main.bicep`. A aplicacao demonstra Speech, Language e Service Bus.

---

## Privacidade, Etica e Design Trauma-Informado

### Privacidade (Conformidade LGPD)

- **Pseudonimizacao**: `patient_id` e um hash sem vinculo com identidade real.
- **Criptografia**: Azure Storage com TLS 1.2+ em transito e criptografia em repouso.
- **Minimizacao de dados**: Apenas scores e evidencias sao persistidos; midia bruta nao e armazenada na nuvem.
- **Retencao**: Politicas de ciclo de vida no Blob Storage e controle de expiracao por metadados.
- **Direito ao apagamento**: Suporte a exclusao por `patient_id`.

### Design Trauma-Informado

- O sistema **nunca diagnostica** violencia domestica automaticamente.
- Todas as saidas sao enquadradas como sinais para revisao humana, nao conclusoes.
- Trilhas de cuidado usam linguagem nao-julgadora.
- Guardrails sao embutidas em cada saida de avaliacao de cuidado.
- O campo `reviewFocus` sugere topicos de conversa, nao acusacoes.

### Guardrails (embutidas em toda saida)

1. Nao diagnosticar automaticamente violencia domestica.
2. Priorizar revisao humana.
3. Considerar falsos positivos e contexto.

---

## Limitacoes

- **Dados de fala atuada**: Modelos de emocao por audio treinados em RAVDESS, limitando generalizacao para fala espontanea.
- **Contexto de video educacional**: DAiSEE representa cenarios educacionais, nao clinicos.
- **Cobertura do lexico portugues**: Analise de texto depende de lista curada; expressoes de baixa frequencia ou regionais podem ser perdidas.
- **Fusao multimodal por sessao**: o pipeline ja inclui anomalia temporal clinica, mas a fusao entre modalidades ainda e calculada por analise/sessao.
- **Inferencia somente CPU**: Modelos intencionalmente leves; tradeoffs de acuracia documentados.
- **Pose de pessoa unica**: Heuristica de postura defensiva avalia apenas a pessoa de maior confianca.
- **Sem validacao clinica real**: O sistema nao foi testado em ambientes clinicos.

---

## Roadmap

### Concluido nesta fase

- [x] Implementar logging JSON estruturado com correlation IDs.
- [x] Construir frontend React com dashboard multimodal.
- [x] Integrar 5a modalidade (clinico/obstetrico).
- [x] Gerar manifests e evidencias para 6 datasets.
- [x] Treinar e avaliar YOLOv8n no dataset de objetos cortantes (mAP@50: 87.9%, mAP@50-95: 60.6%).
- [x] Implementar adaptadores Azure para Speech, Language e Service Bus.

### Proximos passos

- [ ] Substituir lexico de texto por BERTimbau para NLP contextual em portugues.
- [ ] Adicionar MFCCs e features espectrais para melhorar baseline de emocao por audio.
- [ ] Solicitar acesso formal a DAIC-WOZ e WEMAC completo para validacao cross-dominio.
- [ ] Implementar fusao baseada em atencao quando dados multimodais temporalmente alinhados estiverem disponiveis.
- [ ] Adicionar testes de integracao com fixtures de teste multimodal sinteticas.

---

## Citacao

```bibtex
@software{sentinela_ai_2025,
  title     = {Sentinela AI: Sistema Multimodal de Apoio a Seguranca Publica e Protecao Integral da Mulher},
  author    = {POSTECH IADT Team},
  year      = {2025},
  url       = {https://github.com/your-username/sentinela-ai},
  note      = {Tech Challenge Fase 4 — IA Multimodal para deteccao preventiva de distress psicologico e vulnerabilidade comportamental}
}
```

---

## Agradecimentos

- [POSTECH](https://postech.fiap.com.br/) — Programa IADT e framework do Tech Challenge.
- [Ultralytics](https://ultralytics.com/) — Arquitetura de modelos YOLOv8.
- [OpenAI Whisper](https://github.com/openai/whisper) — Transcricao de fala para texto.
- [RAVDESS](https://zenodo.org/record/1188976), [DAiSEE](https://iith.ac.in/~daisee/), [EATD-Corpus](https://github.com/speechandlanguageprocessing/ICASSP2022-Depression) — Datasets publicos.
- [Roboflow](https://roboflow.com/) — Dataset de deteccao de objetos cortantes.

---

---

# English

**Multimodal Safety and Wellbeing Monitor for Women's Health**

Sentinela AI is a multimodal inference system that combines reports, audio, video, images, and clinical data to identify risk and vulnerability signals, supporting public safety and comprehensive protection for women. It generates auditable reports with trauma-informed care pathways and human review safeguards.

---

## Problem Statement

Domestic violence against women frequently manifests through indirect signals: vocal hesitation, altered tone, defensive body postures, the presence of sharp objects in the environment, and linguistic markers of fear, control, or isolation. These signals appear across multiple modalities and rarely in a single data source.

Clinical teams need tools that can synthesize heterogeneous signals into actionable triage indicators — without making diagnostic claims, without replacing human judgment, and without exposing sensitive data.

### Key Differentiators

- **5-modality late fusion** (text, audio, video, objects, clinical) with confidence-weighted normalization and coverage penalty.
- **Trauma-informed care layer** translating scores into actionable pathways (not diagnoses).
- **Graceful degradation** — works with any subset of modalities, adjusting confidence accordingly.
- **Academically honest** — all model limitations, biases, and baseline constraints are documented.
- **React + FastAPI interface** — modern dashboard with multimodal visualization and explainability.
- **Azure-first architecture** — production-grade cloud integration aligned with the proposed Sentinela solution.
- **Structured logging** — JSON pipeline tracing with correlation ID and stage-level timing.

---

## Architecture

```
                          +--------------------+
                          |  Input Sources     |
                          |  (audio, text,     |
                          |   video, images)   |
                          +--------+-----------+
                                   |
                    +--------------+--------------+
                    |              |              |              |
              +-----+----+  +----+-----+  +-----+----+  +------+-----+
              |  Audio   |  |   Text   |  |  Video   |  |  Objects   |
              | Extractor|  | Extractor|  | Extractor|  |  Detector  |
              +-----+----+  +----+-----+  +-----+----+  +------+-----+
                    |              |              |              |
                    |         ModalityScore       |              |
                    +--------------+--------------+--------------+
                                   |
                          +--------+---------+
                          |  Fusion Engine   |
                          |  (late fusion,   |
                          |   weighted by    |
                          |   confidence)    |
                          +--------+---------+
                                   |
                    +--------------+--------------+
                    |                             |
              +-----+------+            +--------+--------+
              | Risk Engine|            |  Care Engine    |
              | (triage)   |            | (trauma-informed|
              +-----+------+            |  pathways)      |
                    |                    +--------+--------+
                    |                             |
                    +-----------------------------+
                                   |
                          +--------+---------+
                          |   RiskReport     |
                          |   (JSON output)  |
                          +------------------+
```

### Modalities

| Modality | Input                            | Extractors                                                                  | Signals                                                                   |
| -------- | -------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Audio    | WAV files                        | Acoustic features (RMS, ZCR, silence, clipping) + emotion baseline (LogReg) | Vocal stress, emotional distress, pause patterns                          |
| Text     | Transcripts (PT-BR)              | Lexicon-based multi-label NLP with negation detection                       | Safety concern, coercion, isolation, hopelessness, psychological distress |
| Video    | Pose JSON / frames / video files | YOLOv8-Pose (defensive posture), motion energy, DAiSEE visual wellbeing     | Defensive posture, agitation, boredom/confusion/frustration               |
| Objects  | Images / video frames            | YOLOv8n fine-tuned on sharp objects (15 classes)                            | Environmental threat (knives, scissors, etc.)                             |

### Fusion Strategy

Late fusion with confidence-weighted normalization:

$$s_{mm} = \sum_{m} w_m^{norm} \cdot s_m \cdot \text{coverage\\_penalty}(n)$$

Where weights are modulated by per-modality confidence, and a coverage penalty reduces the fused score when fewer modalities are available (1 mod: 0.88, 2: 0.94, 3: 0.97, 4: 0.99, 5: 1.0).

---

## Features

- **Risk Detection**: Multi-level triage (ROTINA / MONITORAR / URGENTE) with anomaly flags.
- **Audio Analysis**: Acoustic feature extraction + emotion baseline (6 emotions from RAVDESS).
- **Text Analysis**: Portuguese lexicon-based multi-label signal detection with negation handling.
- **Pose Analysis**: COCO17 keypoint defensive posture heuristic with temporal aggregation.
- **Motion Analysis**: Frame-by-frame pixel difference with configurable calibration.
- **Visual Wellbeing**: DAiSEE-based boredom/engagement/confusion/frustration prediction.
- **Object Detection**: YOLOv8n fine-tuned on 15 classes of sharp/dangerous objects.
- **Fusion Engine**: 5-modality late fusion with coverage penalty and confidence modulation.
- **Care Engine**: Trauma-informed assessment with 9 dimensions and 4 care pathways.
- **Clinical Risk**: Obstetric modality with CTG and Maternal Health Risk (WHO thresholds).
- **Human Review**: Audit trail for clinical review (PENDING/CONFIRMED/DISMISSED/ESCALATED).
- **Cloud Integration**: Azure AI Services, Blob Storage, Service Bus, and Key Vault.
- **React Dashboard**: Interactive frontend with multimodal visualization and explainability.
- **Observability**: Structured JSON logging with correlation ID and per-stage metrics.

---

## Technical Stack

| Category    | Technologies                                                       |
| ----------- | ------------------------------------------------------------------ |
| Language    | Python 3.10+                                                       |
| ML / Vision | Ultralytics YOLOv8, scikit-learn, OpenCV, NumPy, Pandas            |
| Audio       | OpenAI Whisper (transcription), custom acoustic feature extraction |
| API         | FastAPI, Uvicorn, Pydantic                                         |
| Frontend    | React 18, TypeScript, Vite, Tailwind CSS, Recharts                 |
| Cloud       | Azure AI Services, Blob Storage, Service Bus, Key Vault |
| Data        | yt-dlp, joblib, PyYAML                                             |
| Testing     | unittest (56 tests)                                                |

---

## Installation

### Prerequisites

- Python 3.10 or higher
- `ffmpeg` in PATH (for audio processing)
- Git

### Setup

```bash
git clone <repository-url>
cd "Tech Challenge IADT - Fase 4"

python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Usage

### Official Interface (React + FastAPI)

**1. Start backend:**

```bash
cd backend
uvicorn main:app --reload --port 8000
```

> **Note:** Install root dependencies first (`pip install -r requirements.txt`). The `backend/requirements.txt` only contains FastAPI-specific packages; the backend imports the full `src/` package.

**2. Start frontend:**

```bash
cd frontend
npm install
npm run dev
```

**3. Open browser:** `http://localhost:5173`

The dashboard accepts 5 input types: text, audio (WAV), video (MP4/AVI/MOV), image (JPG/PNG), and clinical data (vital signs form).

### CLI

```bash
# Text-only analysis
python -m src.cli --transcript data/transcripts/sample.txt

# Full multimodal (all inputs)
python -m src.cli \
  --transcript data/transcripts/sample.txt \
  --audio-wav data/audio/sample.wav \
  --pose-json data/pose/pose_keypoints.json \
  --image-for-objects test_image.jpg \
  --out data/results/full_report.json
```

### API

The full API (with report listing and human review endpoints) is in `src/api/app.py`:

```bash
uvicorn src.api.app:app --reload --port 8000
```

| Method | Path                        | Description              | App             |
| ------ | --------------------------- | ------------------------ | --------------- |
| GET    | `/health`                   | Health check             | backend/main.py |
| POST   | `/analyze`                  | Run multimodal analysis  | backend/main.py |
| GET    | `/api/health`               | Health check             | src/api/app.py  |
| POST   | `/api/analyze`              | Run multimodal analysis  | src/api/app.py  |
| GET    | `/api/reports`              | List saved reports       | src/api/app.py  |
| GET    | `/api/report/{name}`        | Retrieve specific report | src/api/app.py  |
| POST   | `/api/report/{name}/review` | Record human review      | src/api/app.py  |

---

## Model Strategy

### Baselines (intentionally simple and explainable)

| Model                     | Type                | Accuracy     | Macro-F1        | Rationale                                                       |
| ------------------------- | ------------------- | ------------ | --------------- | --------------------------------------------------------------- |
| Audio Emotion             | Logistic Regression | 42.7%        | 38.7%           | Simple, explainable; acoustic features only                     |
| Visual Wellbeing (DAiSEE) | Random Forest       | 59.6%        | 23.1%           | Interpretable baseline; F1 reflects class imbalance honestly    |
| Text Signals              | Lexicon-based       | N/A          | N/A             | Rule-based; precision depends on vocabulary coverage            |
| Sharp Objects             | YOLOv8n             | mAP50: 87.9% | mAP50-95: 60.6% | Fine-tuned 10 epochs, 15 classes, Precision 84.2%, Recall 81.1% |
| Defensive Posture         | Heuristic           | N/A          | N/A             | Geometry-based; no trained classifier                           |

### Why baselines, not deep learning?

1. **Explainability over accuracy** in a sensitive clinical domain.
2. **Reproducibility** without GPU requirements.
3. **Auditability** — every score can be traced to specific features.
4. **Honest documentation** — we report what the models can and cannot do.

---

## Testing

```bash
python -m unittest discover -s tests -v
```

56 tests covering:

- **Labels & Manifests** (27 tests): Sentinela taxonomy, RAVDESS/EATD/CTG/Maternal mappings, manifest I/O.
- **Clinical Extractor**: CTG (Normal/Suspect/Pathological), Maternal Risk (low/mid/high), vital signs.
- **Fusion (5 modalities)**: clinical-only, clinical+text, full 5-modality coverage.
- **Care Engine**: obstetric pathway, obstetricRisk dimension, review focus.
- **Pipeline Integration**: clinical data through pipeline, text+clinical multimodal.
- **Object Detection**: detection, COCO fallback, risk escalation, human review.
- **Text/Audio/Video**: text signals, fusion, coverage penalty.
- **API**: health check, endpoints.

---

## Azure Cloud Architecture

| Service | Role |
| --- | --- |
| Azure AI Services | Real Speech-to-Text and Language sentiment/key phrase enrichment |
| Blob Storage | Encrypted report and evidence envelope storage |
| Service Bus | Real clinical alert queue when the send connection string is configured |
| Key Vault | Secrets and integration keys |
| Log Analytics + Application Insights | Observability |

> **Status:** Bicep template available at `infra/azure/main.bicep`. The application demonstrates Speech, Language and Service Bus integration.

---

## Privacy, Ethics, and Trauma-Informed Design

- **Pseudonymization**: `patient_id` is a hash with no link to real identity.
- **Encryption**: Azure Storage encryption at rest and TLS 1.2+ in transit.
- **Data minimization**: Only scores and evidence are persisted; raw media is not stored in the cloud.
- The system **never diagnoses** domestic violence automatically.
- All outputs are framed as signals for human review, not conclusions.
- Care pathways use non-judgmental language with embedded guardrails.

---

## Limitations

- **Acted speech data**: Audio emotion models trained on RAVDESS (acted), limiting generalization to spontaneous speech.
- **Educational video context**: DAiSEE represents educational settings, not clinical environments.
- **Portuguese lexicon coverage**: Text analysis depends on a curated term list; low-frequency or regional expressions may be missed.
- **Session-level multimodal fusion**: clinical time-series anomaly detection is implemented, while cross-modality fusion is still computed per analysis session.
- **CPU-only inference**: Models are intentionally lightweight; accuracy tradeoffs are documented.
- **No real clinical validation**: The system has not been tested in clinical settings.

---

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Write tests for new functionality.
4. Ensure all existing tests pass (`python -m unittest discover -s tests`).
5. Submit a pull request with a clear description.

---

## License

This project was developed as part of the POSTECH IADT Tech Challenge (Phase 4). License terms to be defined.
