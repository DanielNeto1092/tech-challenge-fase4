# Referencia: felipewww/ai-pos-4

Repositorio analisado: https://github.com/felipewww/ai-pos-4

## Pontos aproveitaveis

- Separar o projeto em pipeline/orquestracao e `Risk Engine`.
- Usar modelo local explicavel para priorizacao, como Logistic Regression.
- Salvar metricas, matriz de confusao e modelo versionavel.
- Retornar `confidence` e acionar Human-in-the-Loop quando houver risco alto ou baixa confianca.
- Documentar que a decisao sensivel nao e automatizada de forma final.

## Diferenca para este projeto

O projeto de referencia e centrado em audio/transcricao/AWS Comprehend. Este projeto avanca em uma proposta multimodal local:

- audio: features acusticas e baseline emocional;
- video: pose, postura defensiva e movimento;
- texto: marcadores contextuais e risco psicologico;
- fusao: score multimodal auditavel;
- governanca: recomendacao de revisao humana para alertas e baixa confianca.

## Proxima incorporacao recomendada

Criar uma camada `Risk Engine` formal que transforme sinais das modalidades em:

- `ROTINA`
- `MONITORAR`
- `URGENTE`

Essa camada deve usar probabilidades/confianca e regras de HITL inspiradas na referencia.
