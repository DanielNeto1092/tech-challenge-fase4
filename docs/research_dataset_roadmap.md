# Roadmap de Datasets de Pesquisa

Esta lista organiza bases publicas, academicas e de acesso controlado que fortalecem o Sentinela como projeto de pesquisa multimodal.

## Conversacao emocional e contexto

| Dataset | Modalidades | Valor para o projeto | Status |
| --- | --- | --- | --- |
| MELD | texto, audio, video | emocao em dialogos multi-party; NLP contextual | recomendado |
| IEMOCAP | audio, video, mocap, dialogo | emocao em interacao diadica, mais natural que RAVDESS | acesso controlado |
| CMU-MOSEI | texto, audio, video | sentimento/emocao em videos naturais | recomendado |

## Saude mental, distress e stress

| Dataset/Challenge | Modalidades | Valor para o projeto | Status |
| --- | --- | --- | --- |
| DAIC-WOZ | texto, audio, video | entrevistas clinicas e sinais depressivos | acesso controlado |
| AVEC | multimodal | benchmark de depressao, afeto e distress | recomendado |
| MuSe | multimodal | stress, sentimento, social perception e emotion recognition | recomendado |
| SEWA | texto, audio, video | comportamento espontaneo multicultural | acesso por requisicao |

## Anomalia, comportamento e vigilancia

| Dataset | Modalidades | Valor para o projeto | Status |
| --- | --- | --- | --- |
| DAiSEE | video | bem-estar visual indireto: tedio, engajamento, confusao, frustracao | local |
| UCF-Crime | video | anomalia visual e movimento | local |
| UCA | video + linguagem | descricoes semanticas e temporais do UCF-Crime | recomendado |
| HR-Crime | video | anomalias humanas em vigilancia | recomendado |

## Perspectiva feminina

| Dataset | Modalidades | Valor para o projeto | Status |
| --- | --- | --- | --- |
| WEMAC | multimodal | computacao afetiva com mulheres e perspectiva de genero | acesso com DUA/senha |
| UC3M4Safety | metadados/estimulos | fundamentacao de genero e estimulos audiovisuais | local |

## Decisao metodologica

O Sentinela deve usar late fusion inicialmente, pois os datasets sao heterogeneos, nem sempre sincronizados e frequentemente possuem modalidades faltantes. Early fusion deve ficar como extensao futura.

## Arquitetura futura

- Audio: wav2vec2, HuBERT ou OpenSMILE.
- Texto PT-BR: BERTimbau e embeddings contextuais.
- Video: Video Swin Transformer, TimeSformer ou ViViT.
- Fusao: late fusion ponderada por confianca, depois attention fusion.

## Posicionamento academico

O objetivo nao e "treinar um detector de violencia domestica". O objetivo e criar uma arquitetura de inferencia multimodal de vulnerabilidade emocional, sofrimento psicologico e risco comportamental, com revisao humana e comunicacao trauma-informada.
