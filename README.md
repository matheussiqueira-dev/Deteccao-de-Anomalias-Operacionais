# Operational Anomaly Radar (MVP)

Sistema de monitoramento operacional em tempo real com detecção automática de anomalias.

## Estrutura
- `backend/` FastAPI + Isolation Forest + TimescaleDB + arquitetura em camadas
- `frontend/` React + D3 com painel interativo
- `.github/` pipeline CI

## Arquitetura (camadas)
- **API**: `backend/app/api` (rotas REST/WS)
- **Domínio**: `backend/app/domain` (entidades e contratos)
- **Serviços**: `backend/app/services` (casos de uso/negócio)
- **Infra**: `backend/app/database` e `backend/app/services/kafka_consumer.py`
- **Modelos IA**: `backend/app/ml_models`

## Backend

### Requisitos
- Python 3.11 recomendado (wheels disponíveis para scikit-learn/psycopg2)
- PostgreSQL + TimescaleDB
- Docker (opcional para subir DB/API)

### Configuração
1. Copie `backend/.env.example` para `backend/.env` e ajuste as variáveis.
2. Instale dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
```

Autoencoder (opcional):
```bash
pip install -r backend/requirements-ml.txt
```

### Executar
```bash
cd backend
uvicorn app.main:app --reload
```

### Docker Compose (API + TimescaleDB + Frontend)
```bash
docker compose up --build
```
Use `backend/.env` para sobrescrever variáveis no serviço `api` se necessário.

### WebSocket ingest (MVP)
Envie payloads para `ws://localhost:8000/ws/ingest` no formato:
```json
{
  "timestamp": "2026-01-30T15:45:12Z",
  "source": "finance",
  "metric_name": "revenue_variation",
  "value": 9.6,
  "unit": "percent",
  "tags": ["region=SP", "team=alpha"]
}
```

### Alertas em tempo real (WS)
O backend envia alertas em `ws://localhost:8000/ws/alerts` no formato:
```json
{
  "type": "alert",
  "data": {
    "metric": "revenue_variation",
    "score": 0.92,
    "value": 9.6,
    "timestamp": "2026-01-30T15:45:12Z",
    "source": "finance"
  }
}
```

### Endpoints principais
- `POST /auth/login` (opcional no MVP)
- `POST /metrics/ingest`
- `GET /metrics/history`
- `GET /anomalies/latest`
- `POST /train` (requer `metric_name` e `source`)
- `WS /ws/alerts`
- `WS /ws/ingest`
- `WS /ws/health`
- `GET /health`

### Exemplo de ingestão
```json
{
  "timestamp": "2026-01-30T15:45:12Z",
  "source": "finance",
  "metric_name": "revenue_variation",
  "value": 9.6,
  "unit": "percent",
  "tags": ["region=SP", "team=alpha"]
}
```

## Frontend

### Requisitos
- Node 18+

### Instalar e rodar
```bash
cd frontend
npm install
npm run dev
```

Configuração do backend via `VITE_API_URL` no `.env`:
```
VITE_API_URL=http://localhost:8000
```

Login padrão (MVP):
- usuário: `admin`
- senha: `radar`

## Observabilidade
- Logs estruturados em JSON via `structlog`
- Métricas Prometheus em `/metrics` (habilite com `METRICS_ENABLED=true`)
- Health checks em `/health` e `ws://.../ws/health`
 - Prometheus: http://localhost:9090
 - Grafana: http://localhost:3000 (admin/admin)

## Qualidade de código
```bash
black --check backend
isort --check-only backend
flake8 backend
pytest backend
```

CI configurado em `.github/workflows/ci.yml`.

## Observações
- O detector Isolation Forest é treinado automaticamente após acumular dados suficientes.
- Autoencoder disponível via `AUTOENCODER_ENABLED=true` e `MODEL_STRATEGY=autoencoder|hybrid`.
- Kafka é opcional (habilite via `KAFKA_ENABLED=true`).

## Monitoramento (planejado)
- **Prometheus**: métricas de ingestão, latência e alertas/minuto.
- **Grafana**: dashboards operacionais e alertas visuais.
- **Reprocessamento**: endpoint `/train` para re-treinamento em lote.
