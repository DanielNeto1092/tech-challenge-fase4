# Arquitetura Azure - Tech Challenge Fase 4

## Objetivo

A entrega usa o pipeline local do Sentinela AI para processar evidencias multimodais e empacota cada resultado em um envelope compativel com uma operacao em Azure. O modo padrao e `local_simulation`, suficiente para demonstracao sem credenciais. Com variaveis de ambiente Azure preenchidas, o mesmo contrato identifica a configuracao pronta para adaptadores reais.

## Servicos gerenciados mapeados

| Modalidade ou etapa | Servico Azure proposto | Papel na solucao |
| --- | --- | --- |
| Video clinico e consulta | Azure AI Vision / Custom Vision | Apoiar inferencia visual, artefatos YOLOv8 e analise de frames. |
| Audio de consulta | Azure AI Speech | Transcricao e enriquecimento de sinais de fala. |
| Texto clinico | Azure AI Language | Analise de linguagem, sentimento e sinais de risco em texto. |
| Dados clinicos | Azure Health Data Services | Envelope interoperavel para sinais vitais e dados obstetricos. |
| Relatorios | Azure Blob Storage | Armazenamento criptografado de relatorios JSON. |
| Alerta a equipe medica | Azure Service Bus | Fila para encaminhar casos com risco alto ou revisao humana. |
| Segredos | Azure Key Vault | Controle de chaves e credenciais. |

## Variaveis de ambiente

```bash
export AZURE_REGION=brazilsouth
export AZURE_COGNITIVE_ENDPOINT=https://<recurso>.cognitiveservices.azure.com/
export AZURE_COGNITIVE_KEY=<chave>
export AZURE_STORAGE_ACCOUNT=<conta>
export AZURE_STORAGE_CONTAINER=sentinela-reports
export AZURE_SERVICE_BUS_NAMESPACE=<namespace>
export AZURE_SERVICE_BUS_QUEUE=clinical-alerts
export AZURE_KEY_VAULT_NAME=<key-vault>
```

## Fluxo de alerta

1. Frontend envia texto, audio, video, imagem e/ou dados clinicos para `POST /analyze`.
2. O pipeline executa extratores especializados e fusao tardia.
3. O motor de risco define prioridade e necessidade de revisao humana.
4. `src/cloud/azure_integration.py` gera `_azure_integration`.
5. Se o nivel for alto/critico ou `humanReviewRequired=true`, o alerta fica com status `queued_for_medical_team`.

## Privacidade e seguranca

- Minimizacao de dados e pseudonimo `case_id`.
- Hash do payload para rastreabilidade sem expor conteudo sensivel.
- Linguagem de triagem, nao diagnostica.
- Revisao humana antes de qualquer conduta clinica.
- Limite de armazenamento criptografado no desenho de cloud.
