# Aderencia ao PDF - Tech Challenge Fase 4

## Escolhas do projeto

O projeto implementa mais do que o minimo solicitado:

- Funcionalidades escolhidas: video, audio, sinais vitais clinicos, texto e integracao em nuvem.
- Objetivos cobertos: risco materno/ginecologico, violencia domestica/abuso, bem-estar psicologico, nuvem gerenciada e anomalias preventivas.
- Modelo YOLOv8 escolhido: objetos suspeitos/cortantes que possam indicar risco ambiental, automutilacao ou violencia.

## Entregas tecnicas

| Exigencia do enunciado | Implementacao |
| --- | --- |
| Analise de videos clinicos | `PoseExtractor`, `MotionExtractor`, `VisualWellbeingExtractor` e metadados de processamento de video na API. |
| Sinais nao verbais de desconforto ou medo | Heuristicas de postura defensiva, movimento e bem-estar visual. |
| Triagem de violencia | Texto, audio, postura e objetos alimentam score de vulnerabilidade e revisao humana. |
| YOLOv8 customizado ou proposto | Detector de objetos cortantes com YOLOv8 customizavel e fallback COCO. |
| Relatorios automaticos especializados | Saida JSON com score, nivel, motivos, prioridades, trilhas de cuidado, trace e envelope Azure. |
| Analise de audio | Features acusticas, pausas/silencio, clipping e baseline emocional. |
| Depressao pos-parto, ansiedade, trauma | Sinais de distress no texto/audio e trilhas de cuidado trauma-informadas. |
| Integracao Azure | `_azure_integration` na resposta da API, docs de arquitetura e variaveis de ambiente. |
| Fluxo final do alerta | Status `queued_for_medical_team` quando o risco exige revisao. |

## Como demonstrar em ate 15 minutos

1. Mostrar o PDF e a matriz de aderencia.
2. Subir backend e frontend.
3. Inserir relato com medo/ansiedade, audio ou video curto e sinais clinicos.
4. Executar analise.
5. Explicar scores por modalidade, fusao, prioridade, trilha de cuidado e `_azure_integration`.
6. Destacar que o sistema e apoio a triagem, nao diagnostico automatico.
