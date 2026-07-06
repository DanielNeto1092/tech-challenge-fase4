# Estrategia com Bases Publicas

O projeto deve priorizar bases publicas e reais, evitando criar casos sinteticos para demonstracao principal. Como datasets reais de violencia domestica multimodal sao raros e sensiveis, a estrategia e combinar bases publicas de sinais correlatos.

## Bases publicas ja disponiveis localmente

| Base | Modalidade | Tarefa | Uso no Sentinela |
| --- | --- | --- | --- |
| RAVDESS | audio, video | emocao atuada | baseline de emocao vocal/facial |
| CREMA-D | audio, video | emocao audiovisual | baseline emocional com diversidade maior |
| DAiSEE | video | boredom, engagement, confusion, frustration | bem-estar/estado afetivo visual indireto |
| UCF-Crime frames | video/frames | anomalia visual | movimento/anomalia visual exploratoria |
| UC3M4Safety metadata | metadados | estimulos com perspectiva de genero | fundamentacao teorica |

## Bases recomendadas para violencia/anomalia sem usar UCF-Crime como semantica principal

| Base | Modalidade | Papel correto |
| --- | --- | --- |
| Hockey Fight Dataset | video | baseline simples de violence/non-violence em contexto esportivo |
| Real Life Violence Situations | video | baseline violence/non-violence com videos reais |
| UCA | video + linguagem | anotacao semantica/temporal do UCF-Crime para video-language learning |
| HR-Crime | video/features | subset human-related do UCF-Crime para anomalia humana |

## Bases de acesso controlado

| Base | Status | Uso desejado |
| --- | --- | --- |
| WEMAC | publico com arquivos criptografados/DUA | sinais multimodais femininos e perspectiva de genero |
| DAIC-WOZ | acesso por formulario academico | sofrimento psicologico/depressao multimodal |

## Papel de cada base no projeto

### Emocao e sofrimento afetivo

Usar RAVDESS e CREMA-D para treinar e avaliar modelos de emocao. Esses datasets nao representam trauma real, mas fornecem um ponto de partida publico e rotulado.

### Bem-estar e comportamento visual

Usar DAiSEE para sinais de engajamento, confusao, frustracao e tedio. Esses sinais nao indicam violencia, mas ajudam a construir uma camada de bem-estar/estado afetivo visual.

### Anomalia visual

Usar UCF-Crime apenas como baseline exploratorio de anomalia/movimento. Nao apresentar como detector de violencia domestica.

Uso recomendado do UCF-Crime:

- pretreino de encoder visual;
- motion anomaly pretraining;
- temporal anomaly learning;
- comparacao com UCA/HR-Crime quando disponiveis.

Uso nao recomendado:

- dataset semantico principal;
- evidencia direta de violencia domestica;
- proxy de sofrimento psicologico feminino.

### Perspectiva de genero

Usar UC3M4Safety/WEMAC como fundamentacao teorica e, se o acesso for aprovado, como base especializada.

## Posicionamento academico

O Sentinela nao detecta violencia domestica diretamente. Ela combina sinais publicamente estudados de emocao, sofrimento, engajamento, postura e anomalia para apoiar acolhimento e revisao humana.

## O que nao fazer

- Nao chamar UCF-Crime de dataset de violencia domestica.
- Nao tratar DAiSEE como base clinica.
- Nao afirmar diagnostico de depressao, abuso ou trauma.
- Nao usar dados sinteticos como evidencia principal do desempenho.
