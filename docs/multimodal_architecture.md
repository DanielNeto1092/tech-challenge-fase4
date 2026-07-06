# Arquitetura Multimodal Proposta

Esta arquitetura posiciona o Sentinela como um sistema de inferencia multimodal de vulnerabilidade emocional, sofrimento psicologico e risco comportamental feminino.

## Principio central

Nao fazer early fusion no MVP. As bases sao heterogeneas, possuem modalidades faltantes e diferentes niveis de sincronizacao temporal. A estrategia inicial e:

1. extrair sinais por modalidade;
2. calibrar confianca por modalidade;
3. aplicar late fusion auditavel;
4. evoluir para attention fusion quando houver dados suficientes.

## Backbones recomendados

### Video

| Backbone | Uso futuro |
| --- | --- |
| Video Swin Transformer | representacao espaco-temporal robusta |
| TimeSformer | atencao temporal para sequencias de video |
| ViViT | transformer de video para modelagem temporal |

No MVP, o Sentinela usa features auditaveis de movimento, pose e DAiSEE visual baseline. Esses modelos profundos entram como evolucao.

### Audio

| Backbone | Uso futuro |
| --- | --- |
| wav2vec2 | representacao auto-supervisionada de fala |
| HuBERT | embeddings robustos de fala |
| OpenSMILE | features acusticas padronizadas para affective computing |

No MVP, o Sentinela usa energia, pausas, ZCR, variabilidade e baseline emocional acustico.

### Texto

| Backbone | Uso futuro |
| --- | --- |
| BERTimbau | embeddings contextuais em PT-BR |
| LLM embeddings | marcadores contextuais, relatos e sumarizacao |

No MVP, o Sentinela usa marcadores auditaveis em portugues e normalizacao de acentos.

## Fusion

### Atual

Late fusion ponderada por confianca:

- aceita modalidades ausentes;
- preserva explicabilidade;
- facilita auditoria;
- reduz risco de overfitting em datasets desalinhados.

### Futuro

Attention fusion:

- pesos dinamicos por janela temporal;
- atencao entre texto, audio e video;
- tratamento explicito de incerteza e missing modalities.

## Stack de datasets por camada

| Camada | Bases |
| --- | --- |
| Core emocional | RAVDESS, CREMA-D, IEMOCAP, MELD |
| Saude mental/distress | DAIC-WOZ, AVEC, MuSe |
| Generalizacao natural | CMU-MOSEI, SEWA |
| Anomalia/comportamento | DAiSEE, UCF-Crime, HR-Crime, UCA |
| Perspectiva feminina | WEMAC, UC3M4Safety |

## Como defender para a banca

O ponto forte nao e alegar um detector final de violencia. O ponto forte e demonstrar dominio sobre:

- limitacoes dos datasets;
- acted vs in-the-wild;
- vies de genero;
- explainability;
- falso positivo e falso negativo;
- incerteza multimodal;
- revisao humana;
- comunicacao trauma-informada.
