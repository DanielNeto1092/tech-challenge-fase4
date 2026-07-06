# Demo Narrativa - Sentinela AI

## Cenario

Uma profissional de saude recebe uma gravacao, transcricao ou video curto de uma paciente. A paciente nao precisa declarar explicitamente uma situacao de violencia para que o sistema observe sinais indiretos de sofrimento, vulnerabilidade ou necessidade de acolhimento.

## Entrada

O sistema pode receber:

- transcricao textual;
- audio WAV;
- video;
- pose JSON;
- frames extraidos.

## Analise

Cada modalidade gera sinais independentes:

- texto: seguranca, controle/coercao, isolamento, desesperanca, sintomas fisicos e sofrimento psicologico;
- audio: energia, pausas, variabilidade e emocao vocal aproximada;
- video: movimento, postura e bem-estar visual indireto via DAiSEE.

## Fusao

O Sentinela usa late fusion ponderada por confianca. Isso permite que uma modalidade ausente nao invalide a analise.

## Saida

O sistema gera:

- score multimodal;
- prioridade operacional;
- trilha de cuidado;
- dimensoes de bem-estar;
- incerteza;
- evidencias por modalidade;
- foco para revisao humana;
- perguntas cuidadosas;
- checklist de privacidade.

## Como o Sentinela responde com seguranca

Ela nunca diz "violencia detectada". Ela indica que ha sinais que justificam acolhimento, monitoramento ou revisao prioritaria. A decisao sensivel permanece humana.

## Mensagem para banca

A excelencia do projeto esta menos em prometer um modelo perfeito e mais em demonstrar arquitetura, governanca, incerteza, explicabilidade e responsabilidade no uso de IA em um dominio sensivel.
