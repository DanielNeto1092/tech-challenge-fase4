# Datasets do projeto

Este projeto usa uma estrategia multimodal indireta: nao diagnostica violencia domestica, mas estima sinais de sofrimento psicologico, medo, estresse, postura defensiva e vulnerabilidade contextual.

## Bases ja presentes

| Dataset | Pasta local | Modalidades | Uso recomendado |
| --- | --- | --- | --- |
| RAVDESS | `github/ravdess` | audio, video | Bootstrap de reconhecimento emocional. |
| CREMA-D | `github/crema-d` | audio, video | Fine-tuning emocional com maior diversidade vocal/facial. |
| UCF-Crime/Anomaly frames | `archive` | video/frames | Demo de anomalia visual e movimento. Usar com cuidado, pois nao e especifico para violencia domestica. |
| DAiSEE | `archive/DAiSEE` | video | Bem-estar visual indireto: boredom, engagement, confusion, frustration. |
| UC3M4Safety stimuli list | `doi-10.21950-luo1iz` | metadados | Fundamentacao teorica sobre estimulos audiovisuais e violencia de genero. |
| WEMAC signal processing repo | `wemac_dataset_signal_processing-master` | codigo | Referencia de processamento de fala no WEMAC. |

## WEMAC

Referencia principal:

- Scientific Data: https://doi.org/10.1038/s41597-024-04002-8
- Dataverse EMPATIA-CM: https://edatos.consorciomadrono.es/dataverse/empatia

Componentes relevantes:

| Componente | DOI | Status |
| --- | --- | --- |
| Physiological signals | https://doi.org/10.21950/FNUHKE | Publico, mas arquivo principal criptografado. Senha via DUA. |
| Audio features | https://doi.org/10.21950/XKHCCW | Publico, mas arquivo principal criptografado. Senha via DUA. |
| Emotional labelling | https://doi.org/10.21950/RYUCLV | Publico, mas arquivo principal criptografado. Senha via DUA. |
| Biopsychosocial questionnaire | https://doi.org/10.21950/U5DXJR | Publico, mas arquivo principal criptografado. Senha via DUA. |

Observacao etica: o WEMAC e diretamente alinhado ao projeto, pois foi criado no contexto de protecao integral de vitimas de violencia de genero por computacao afetiva multimodal. Mesmo assim, seus arquivos principais exigem acordo de uso.

## DAIC-WOZ

Pagina oficial:

- https://dcapswoz.ict.usc.edu/

Status:

- Nao possui download publico direto.
- A USC informa que a base e distribuida mediante formulario, assinatura/submissao e uso de e-mail academico.
- Por restricoes de consentimento, a distribuicao e limitada a academicos e pesquisadores sem fins lucrativos.

Uso no projeto:

- Excelente base para sofrimento psicologico/depressao.
- Deve entrar como dependencia externa pendente ate a aprovacao de acesso.
- Enquanto nao houver liberacao, o MVP pode usar transcricoes proprias, RAVDESS/CREMA-D para emocao e WEMAC/UC3M4Safety para fundamentacao.

## Justificativa academica

Datasets reais de violencia domestica multimodal sao raros por razoes eticas, legais e de privacidade. Por isso, o projeto deve ser apresentado como deteccao preventiva de vulnerabilidade e sofrimento psicologico, nao como detector definitivo de violencia domestica.
