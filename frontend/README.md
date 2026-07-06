# Sentinela AI — React + FastAPI

## Estrutura

```
backend/
  main.py              ← FastAPI (wrapper para SentinelaPipeline)
  requirements.txt

frontend/
  package.json
  vite.config.ts
  tailwind.config.ts
  index.html
  src/
    main.tsx
    App.tsx
    index.css
    vite-env.d.ts
    types/sentinela.ts
    lib/api.ts
    lib/utils.ts
    components/
      Sidebar.tsx
      Hero.tsx
      FlowSteps.tsx
      CapabilityCards.tsx
      RadarProfile.tsx
      ProcessingState.tsx
      RiskHero.tsx
      ExplainabilityPanel.tsx
      ModalityCards.tsx
      EvidenceTimeline.tsx
      CarePathway.tsx
      Limitations.tsx
```

## Como rodar

### 1. Backend (FastAPI)

```powershell
cd "E:\Tech Challenge IADT - Fase 4"

# Ativar venv existente
.\.venv\Scripts\Activate.ps1

# Instalar deps do backend
pip install fastapi uvicorn python-multipart

# Rodar o backend
cd backend
uvicorn main:app --reload --port 8000
```

O backend roda em `http://127.0.0.1:8000`.  
Teste com `GET http://127.0.0.1:8000/health`.

### 2. Frontend (React)

```powershell
cd "E:\Tech Challenge IADT - Fase 4\frontend"

# Instalar deps
npm install

# Rodar dev server
npm run dev
```

O frontend roda em `http://localhost:5173`.

### Importante

- O backend importa `from src.pipeline import SentinelaPipeline` — ele adiciona o PROJECT_ROOT ao sys.path automaticamente.
- O CORS está configurado para permitir `localhost:5173`.
- Nenhuma lógica de pipeline foi alterada.
