# Arquitetura AWS - Sentinela AI

## Status da implementacao

Esta versao descreve a integracao AWS realmente executada no projeto.

O processamento de IA permaneceu local para evitar custo com GPU ou servicos gerenciados pagos. A AWS foi usada como uma camada serverless de persistencia, indexacao e evidencias operacionais.

Regiao usada: `us-east-1`  
Stack CloudFormation: `sentinela-ai-free-tier`  
Status observado: `CREATE_COMPLETE`

## Servicos usados

| Servico | Recurso | Finalidade |
| --- | --- | --- |
| CloudFormation | `sentinela-ai-free-tier` | Provisionamento rastreavel da infraestrutura |
| S3 | `sentinela-ai-219834006479-us-east-1-reports` | Armazenamento privado dos reports JSON |
| Lambda | `sentinela-ai-report-indexer` | Processamento automatico de eventos do S3 |
| DynamoDB | `sentinela-ai-reports` | Indice consultavel dos reports por paciente |
| CloudWatch Logs | `/aws/lambda/sentinela-ai-report-indexer` | Evidencia de execucao da Lambda |
| SNS | `sentinela-ai-alerts` | Envio de alertas por email |
| AWS Budgets | Budget mensal | Controle preventivo de custo |

## Diagrama de arquitetura AWS validado

```mermaid
flowchart LR
    subgraph LOCAL["Ambiente local - inferencia de IA"]
        A1["Pipeline multimodal\ntexto | audio | video | objetos"]
        A2["Motor de risco\nscore + prioridade + trilha de cuidado"]
        A3["RiskReport JSON\nresultado auditavel"]
        A1 --> A2 --> A3
    end

    subgraph AWS["Conta AWS 219834006479 - Regiao us-east-1"]
        subgraph SEC["Controles transversais"]
            BUD["AWS Budgets\nalertas de custo"]
            CFN["CloudFormation\nstack sentinela-ai-free-tier"]
            IAM["IAM least privilege\npublisher + role da Lambda"]
        end

        subgraph STORAGE["Camada de armazenamento"]
            S3["Amazon S3\nbucket privado de reports\nSSE-S3 + Block Public Access\nLifecycle 30 dias"]
        end

        subgraph EVENT["Camada serverless orientada a evento"]
            EVT["S3 Event Notification\nObjectCreated em results/"]
            LBD["AWS Lambda\nreport-indexer\nPython 3.12 | 128 MB | timeout 10s"]
        end

        subgraph DATA["Camada de indice e consulta"]
            DDB["Amazon DynamoDB\nsentinela-ai-reports\npk=PATIENT#{id}\nsk=TS#{timestamp}\nTTL habilitado"]
        end

        subgraph ALERT["Camada de alerta"]
            SNS["Amazon SNS\nsentinela-ai-alerts\nassinatura por email confirmada"]
            EMAIL["Email inscrito\nalerta operacional"]
        end

        subgraph OBS["Observabilidade"]
            CWL["CloudWatch Logs\n/aws/lambda/sentinela-ai-report-indexer"]
            CWM["Lambda Metrics\ninvocations | duration | errors"]
        end

        CFN -. "provisiona" .-> S3
        CFN -. "provisiona" .-> LBD
        CFN -. "provisiona" .-> DDB
        CFN -. "provisiona" .-> SNS
        IAM -. "permissoes minimas" .-> S3
        IAM -. "permissoes minimas" .-> LBD

        S3 --> EVT --> LBD
        LBD --> DDB
        LBD --> SNS --> EMAIL
        LBD --> CWL
        LBD --> CWM
    end

    A3 -->|"upload JSON\nresults/demo-001/evidence_text_high_risk.json"| S3
```

### Leitura do diagrama

- A inferencia pesada permanece fora da AWS para controlar custo e evitar GPU em cloud.
- O S3 e o ponto de entrada cloud: recebe somente o report JSON, nao midia bruta.
- A arquitetura e event-driven: o upload no S3 dispara a Lambda automaticamente.
- A Lambda nao executa inferencia; ela faz integracao, indexacao e alerta.
- O DynamoDB armazena metadados para historico/consulta, nao o payload completo do exame.
- O SNS envia alerta por email para casos configurados como risco alto ou urgente.
- CloudWatch registra execucao, metricas e troubleshooting da Lambda.
- CloudFormation, IAM e Budget sustentam governanca, reproducibilidade e controle de custo.

## Fluxo tecnico

1. A inferencia multimodal foi executada localmente.
2. O pipeline gerou um report JSON em `data/results/evidence_text_high_risk.json`.
3. O arquivo foi enviado ao S3 em `results/demo-001/evidence_text_high_risk.json`.
4. O bucket S3 disparou automaticamente um evento `ObjectCreated`.
5. A Lambda `sentinela-ai-report-indexer` foi invocada.
6. A Lambda leu o JSON no S3 e gravou um item na tabela DynamoDB.
7. A execucao ficou registrada no CloudWatch Logs e nas metricas da Lambda.

## Evidencias observadas

| Evidencia | Resultado |
| --- | --- |
| CloudFormation | Stack `sentinela-ai-free-tier` criada com status `CREATE_COMPLETE` |
| S3 | Objeto `evidence_text_high_risk.json` presente no bucket de reports |
| DynamoDB | Scan retornou 1 item na tabela `sentinela-ai-reports` |
| Lambda Monitor | Houve invocacoes registradas |
| CloudWatch Logs | Log stream criado para `/aws/lambda/sentinela-ai-report-indexer` |
| Budget | Alertas de custo configurados antes da criacao dos recursos |

## Observacoes importantes

### Upload

O script `scripts/publish_report_aws.py` foi preparado para envio via boto3, mas o envio local apresentou travamento no terminal. Para concluir a evidencia da integracao, o upload do JSON foi feito manualmente pelo console do S3.

### Patient ID

O item validado no DynamoDB apareceu como `PATIENT#unknown`. Isso aconteceu porque o arquivo enviado era o JSON puro do report, sem envelope contendo `patient_id`. A arquitetura suporta o campo `patient_id`, mas o teste manual validou principalmente a cadeia S3 -> Lambda -> DynamoDB.

### SNS

O topico SNS `sentinela-ai-alerts` foi criado e a assinatura por email foi confirmada. Portanto, o SNS pode ser apresentado como componente validado de alerta.

Quando a Lambda identifica um nivel de risco configurado para alerta, ela publica uma mensagem no topico SNS, que encaminha a notificacao para o email inscrito.

### CloudWatch

O CloudWatch confirmou invocacoes da Lambda. Alguns eventos exibiram `JSONDecodeError`, associados a tentativas de processamento de conteudo invalido ou fora do formato esperado. Para a apresentacao, isso deve ser tratado como evidencia de execucao e ponto de melhoria, nao como execucao perfeita.

## Seguranca e custo

Medidas aplicadas:

- Budget configurado antes da criacao dos recursos.
- Uso da regiao unica `us-east-1`.
- S3 com Block Public Access.
- S3 com criptografia SSE-S3.
- Bucket policy negando transporte inseguro.
- Lifecycle no S3 com retencao de 30 dias.
- DynamoDB com TTL.
- DynamoDB com capacidade provisionada minima: 1 RCU / 1 WCU.
- CloudWatch Log Group com retencao de 7 dias.
- Lambda com 128 MB e timeout de 10 segundos.
- Sem EC2 ou servicos de IA pagos na nuvem.

## Como explicar no trabalho

Frase tecnica recomendada:

"Eu mantive a inferencia multimodal local para controlar custo e usei AWS como camada serverless de integracao: o report JSON e armazenado em S3 privado com criptografia SSE-S3, um evento ObjectCreated aciona uma Lambda, a Lambda indexa metadados no DynamoDB, a execucao fica auditavel via CloudWatch Logs e o SNS envia alertas por email para casos configurados como risco alto ou urgente."

## Relacao com o requisito academico

O professor informou que nao era necessario rodar tudo em cloud. A implementacao atende ao criterio porque integra uma parte da solucao de IA com AWS usando servicos serverless reais:

- S3 para persistencia do resultado de IA.
- Lambda para automacao baseada em evento.
- DynamoDB para historico/indexacao.
- CloudWatch para observabilidade.

## Artefatos do projeto

- `infra/aws/free_tier_stack.yaml`: template CloudFormation usado para criar a infraestrutura.
- `scripts/publish_report_aws.py`: script preparado para publicar reports no S3.
- `docs/aws_step_by_step.md`: guia operacional da etapa AWS.
- `docs/Sentinela_AI_AWS_Integration.pptx`: apresentacao da integracao AWS.
- `docs/canva_assets/arquitetura_completa_sentinela_aws.svg`: imagem editavel da arquitetura.
- `docs/canva_assets/fluxo_serverless_aws.svg`: imagem editavel do fluxo serverless.
