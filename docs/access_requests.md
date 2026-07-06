# Acesso a datasets controlados

## WEMAC

O Dataverse do WEMAC permite visualizar metadados publicos, mas o download automatico via API foi bloqueado pelo livro de visitas do dataset. Alem disso, os arquivos principais sao criptografados e exigem senha.

Procedimento recomendado:

1. Acesse o Dataverse EMPATIA-CM: https://edatos.consorciomadrono.es/dataverse/empatia
2. Abra os datasets WEMAC relevantes:
   - Physiological signals: https://doi.org/10.21950/FNUHKE
   - Audio features: https://doi.org/10.21950/XKHCCW
   - Emotional labelling: https://doi.org/10.21950/RYUCLV
   - Questionnaire: https://doi.org/10.21950/U5DXJR
3. Preencha o livro de visitas do Dataverse quando solicitado.
4. Envie o DUA indicado no proprio dataset para `uc3m4safety@uc3m.es` para solicitar a senha dos arquivos criptografados.
5. Depois de receber a senha, salve os arquivos em `data/external/wemac/`.

Modelo curto de e-mail:

```text
Subject: WEMAC dataset access request - academic project

Dear UC3M4Safety team,

I am a postgraduate student in Artificial Intelligence developing an academic project on multimodal early detection of psychological distress and vulnerability in women, with gender-based violence as an application context.

I would like to request access/password instructions for the WEMAC encrypted files. I will use the data only for academic and non-commercial research purposes and will cite the dataset and related publications as required.

Attached is the completed Data Usage Agreement.

Best regards,
[Seu nome]
[Instituicao]
[E-mail academico]
```

## DAIC-WOZ

O DAIC-WOZ nao possui download publico direto. A pagina oficial informa que o download exige formulario assinado e submissao com e-mail academico; por restricoes de consentimento, a distribuicao e limitada a academicos e pesquisadores sem fins lucrativos.

Procedimento recomendado:

1. Acesse https://dcapswoz.ict.usc.edu/
2. Clique em "Apply Now DAIC-WOZ".
3. Use e-mail academico.
4. Explique que o uso e academico, sem fins lucrativos, em deteccao multimodal de sofrimento psicologico.
5. Quando o acesso for aprovado, salve os arquivos em `data/external/daic_woz/`.

Modelo curto de justificativa:

```text
I am requesting DAIC-WOZ access for a postgraduate AI academic project focused on multimodal early detection of psychological distress and vulnerability. The dataset will be used for non-commercial research, model prototyping, and academic reporting. The system will not be presented as a diagnostic tool.
```
