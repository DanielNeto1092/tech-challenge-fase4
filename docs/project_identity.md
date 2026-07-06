# Identidade tecnica do projeto

## Nome conceitual

**Sentinela AI**: sistema multimodal de monitoramento preventivo de bem-estar e vulnerabilidade feminina.

## Diferencial

O projeto nao tenta copiar uma arquitetura centrada apenas em transcricao e classificacao textual. A proposta combina:

- sinais acusticos;
- sinais textuais;
- sinais visuais/posturais;
- fusao auditavel;
- avaliacao de cuidado;
- revisao humana em decisoes sensiveis.

O nome "Sentinela" representa deteccao precoce: sinais iniciais, ainda sutis, que podem orientar acolhimento antes de agravamentos.

## Camada propria: Care Assessment

Além do `riskLevel`, o sistema gera uma avaliacao de cuidado com dimensoes interpretaveis:

- `wellbeingIndex`: indice geral de bem-estar estimado;
- `affectiveDistress`: sofrimento afetivo estimado;
- `safetySignal`: sinal contextual de possivel vulnerabilidade/seguranca;
- `nonverbalAlert`: alerta nao verbal por audio/video;
- `dataQuality`: confiabilidade dos sinais disponiveis;
- `uncertainty`: incerteza operacional.

Essa camada evita linguagem diagnostica e traduz o resultado para um fluxo de acolhimento:

- `acompanhamento_rotina`
- `coleta_adicional`
- `acolhimento_e_monitoramento`
- `revisao_prioritaria`

## Por que isso e mais defensavel

Casos de violencia domestica e sofrimento psicologico exigem cuidado etico. O sistema deve apoiar triagem e revisao, nao substituir julgamento profissional. Por isso, a saida inclui:

- foco sugerido para revisao humana;
- perguntas cuidadosas e nao acusatorias;
- guardrails contra diagnostico automatico;
- qualidade dos dados e incerteza.

## Posicionamento para banca

O projeto deve ser apresentado como uma arquitetura multimodal preventiva, com IA explicavel e governanca humana, nao como classificador definitivo de violencia domestica.
