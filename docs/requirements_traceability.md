# Matriz de Rastreabilidade - Tech Challenge Fase 4

| Requisito                                  | Como o Sentinela AI atende                                                                          | Artefatos                                                                                                                                |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| IA integrada para monitoramento continuo   | Pipeline local processa texto, audio, video e imagens, gera score multimodal.                         | `src/pipeline.py`, `src/engines/fusion_engine.py`                                                                                        |
| Dados multimodais (5 modalidades)          | Suporte a texto, WAV audio, pose JSON, video, imagens, dados clinicos estruturados.                   | `src/extractors/audio.py`, `src/extractors/pose.py`, `src/extractors/text.py`, `src/extractors/objects.py`, `src/extractors/clinical.py` |
| Audio                                      | Extrai energia, pausas, variabilidade e predicao emocional por baseline treinado (RAVDESS/CREMA-D).   | `src/extractors/audio.py`, `src/extractors/audio_emotion.py`                                                                             |
| Video                                      | Analisa postura defensiva (YOLOv8-Pose), energia de movimento e bem-estar visual (DAiSEE).            | `src/extractors/pose.py`, `src/extractors/motion.py`, `src/extractors/visual_wellbeing.py`                                               |
| Texto                                      | Detecta 7 categorias de risco em portugues com negacao contextual e intensificadores.                 | `src/extractors/text.py`                                                                                                                 |
| Deteccao de objetos perigosos              | YOLOv8n COCO fallback (knife, scissors, fork) + modelo custom preparado (15 classes).                 | `src/extractors/objects.py`, `src/training/train_sharp_objects.py`                                                                       |
| Identificar sinais precoces de risco       | Gera score multimodal, prioridade operacional (ROTINA/MONITORAR/URGENTE) e dimensoes de cuidado.      | `data/results/evidence_*.json`                                                                                                           |
| Violencia domestica/abuso como caso de uso | Abordagem indireta: seguranca/vulnerabilidade, sofrimento afetivo, revisao humana obrigatoria.        | `docs/project_identity.md`, `docs/trauma_informed_design.md`                                                                             |
| Bem-estar psicologico feminino             | Inclui wellbeingIndex, affectiveDistress, carePathway com 4 trilhas.                                  | `src/engines/care_engine.py`                                                                                                             |
| Deteccao de anomalias                      | Flags: low_confidence, modality_disagreement, sharp_object_detected, object_detection_unavailable.    | `src/engines/risk_engine.py`                                                                                                             |
| Explicabilidade                            | Relatorio mostra scores por modalidade, pesos normalizados, contribuicao por sinal e guardrails.      | `app_demo.py`, `scripts/render_case_summary.py`                                                                                          |
| Human-in-the-Loop                          | Marca humanReviewRequired, sugere foco de revisao, trilha de auditoria.                               | `src/engines/risk_engine.py`, `src/engines/care_engine.py`                                                                               |
| Abordagem trauma-informada                 | Consentimento, privacidade, linguagem nao diagnostica, perguntas cuidadosas.                          | `docs/trauma_informed_design.md`, `src/engines/care_engine.py`                                                                           |
| Datasets e validacao                       | RAVDESS, EATD-Corpus, DAiSEE, CTG, Maternal Health Risk, XD-Violence, Roboflow.                       | `scripts/build_all_manifests.py`, `data/manifests/`                                                                                      |
| Modelos pre-treinados                      | YOLOv8n COCO, YOLOv8n-Pose COCO17, LogReg emocional, RandomForest DAiSEE.                             | `TECHNICAL_REPORT.md` secao 4.1                                                                                                          |
| Risco obstetrico/fetal                     | Modalidade clinica com CTG (NSP) e Maternal Health Risk (sinais vitais OMS).                          | `src/extractors/clinical.py`, `src/domain/labels.py`                                                                                     |
| Cloud/Azure Cognitive Services             | Envelope de integracao Azure para Vision, Speech, Language, Health Data Services, Blob Storage e fila de alerta. | `src/cloud/azure_integration.py`, `backend/main.py`, `docs/azure_architecture.md`                                                        |
| Fluxo final do alerta a equipe medica       | A API inclui `_azure_integration.alert` com status `queued_for_medical_team` quando ha risco alto ou revisao humana. | `backend/main.py`, `frontend/src/App.tsx`                                                                                                |
| Etica/LGPD                                 | Pseudonimizacao, minimizacao, nao diagnostico, vies documentado, revisao humana.                      | `docs/datasets.md`, `TECHNICAL_REPORT.md` secao 7                                                                                        |
| Testes                                     | 56 testes unitarios cobrindo labels, manifests, clinical, fusion, risk, care, objects, pipeline, API. | `tests/test_refactored.py`, `tests/test_sentinela.py`, `tests/test_clinical_and_datasets.py`                                                |

## Evidencias concretas geradas

| Evidencia                           | Resultado                                 | Arquivo                                               |
| ----------------------------------- | ----------------------------------------- | ----------------------------------------------------- |
| Maternal high risk (SBP=140, BS=13) | Score 0.722, URGENTE, revisao_prioritaria | `data/results/evidence_maternal_high_risk.json`       |
| CTG Pathological (NSP=3)            | Score 0.748, URGENTE, revisao_prioritaria | `data/results/evidence_ctg_pathological.json`         |
| CTG Normal (NSP=1)                  | Score 0.088, ROTINA                       | `data/results/evidence_ctg_normal.json`               |
| Maternal low risk                   | Score 0.106, ROTINA                       | `data/results/evidence_maternal_low_risk.json`        |
| Texto psicologico (medo, ansiedade) | Score 0.441, MONITORAR                    | `data/results/evidence_text_psychological.json`       |
| Multimodal texto + clinical         | Score 0.397, acolhimento_e_monitoramento  | `data/results/evidence_multimodal_text_clinical.json` |
| EATD-Corpus audio (SDS=82.5)        | Processado com sucesso                    | `data/results/evidence_eatd_audio.json`               |
| RAVDESS fearful audio               | Processado com sucesso                    | `data/results/evidence_ravdess_fearful.json`          |
| Fork detectado (COCO, conf 0.891)   | MONITORAR, human review                   | `data/results/evidence_object_fork.json`              |

## Lacunas documentadas (evolucao planejada)

- Melhorar NLP com modelo contextual (BERTimbau) em portugues.
- Adicionar MFCCs e features espectrais ao audio.
- Treinar YOLOv8 customizado com 15 classes (dataset Roboflow preparado).
- Executar demonstracao Azure real ponta a ponta com credenciais de assinatura.
- Integrar classificador treinado com EATD-Corpus para deteccao de depressao.
- Treinar modelo de anomalia visual com XD-Violence.
