# Criminal Network Intelligence Platform (CNIP)

**AI-Powered Criminal Network Analysis System** - Project PS26189

An end-to-end AI-powered system that analyzes structured and unstructured crime-related data to uncover criminal networks, identify key influencers, detect suspicious patterns, and provide actionable intelligence for investigators.

## 🎯 Problem Statement

Modern criminal activities are increasingly organized and interconnected. Criminals operate through networks involving associates, intermediaries, financial channels, communication links, locations, and events. Law enforcement agencies collect large volumes of data from sources such as:
- FIRs and police reports
- Call Detail Records (CDRs)
- Financial transaction records
- Surveillance reports
- Social media intelligence
- Criminal history databases
- Intelligence agency reports

Despite having access to this information, investigators face challenges in identifying hidden relationships because data is fragmented, unstructured, and distributed across multiple systems.

## 🚀 Solution Overview

This platform provides:

1. **Multi-Source Data Ingestion** - Ingest FIRs, CDRs, financial records, surveillance reports, social media data
2. **NLP Entity Extraction** - Extract people, locations, vehicles, phone numbers, organizations, bank accounts
3. **Knowledge Graph Construction** - Build relationship maps showing how entities are connected
4. **Network Analysis & Key Player Identification** - PageRank, Betweenness, Community Detection
5. **Anomaly Detection** - ML-based suspicious pattern detection (Isolation Forest, Graph Neural Networks)
6. **Interactive Visualization** - Force-directed graph, timeline, geospatial views
7. **Investigator Dashboard** - Actionable intelligence with risk scoring and alerts

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Criminal Network Intelligence Platform       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Data       │  │   NLP        │  │   Graph      │          │
│  │   Ingestion  │─▶│   Pipeline   │─▶│   Builder    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Neo4j Knowledge Graph Database                │   │
│  └──────────────────────────────────────────────────────────┘   │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   ML         │  │   Network    │  │   Alert      │          │
│  │   Engine     │  │   Analytics  │  │   Engine     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              FastAPI Backend (REST + WebSocket)           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              React Frontend (Dashboard + Graph Viz)       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
criminal-network-platform/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Config, security
│   │   ├── models/         # Pydantic models
│   │   ├── services/       # Business logic
│   │   └── db/             # Database connections
│   ├── tests/
│   └── requirements.txt
├── frontend/               # React + Vite frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # API services
│   │   └── utils/          # Utilities
│   └── package.json
├── ml/                     # ML models and training
│   ├── models/             # Trained models
│   ├── training/           # Training scripts
│   └── inference/          # Inference pipelines
├── nlp/                    # NLP pipeline
│   ├── extractors/         # Entity extractors
│   ├── processors/         # Text processors
│   └── models/             # Custom NER models
├── data/                   # Data schemas and samples
│   ├── schemas/            # JSON schemas
│   ├── samples/            # Sample data
│   └── migrations/         # DB migrations
├── scripts/                # Utility scripts
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── docs/                   # Documentation
```

## 🛠️ Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | FastAPI, Python 3.11+, Pydantic, Uvicorn |
| **Graph DB** | Neo4j 5.x, Cypher, APOC |
| **NLP** | spaCy, Transformers (BERT), Custom NER |
| **ML/Analytics** | scikit-learn, NetworkX, PyTorch Geometric, PyG |
| **Frontend** | React 19, Vite, TypeScript, D3.js, React Force Graph |
| **Deployment** | Docker, Docker Compose, Kubernetes-ready |
| **Monitoring** | Prometheus, Grafana, Structured Logging |

# Backend Requirements
fastapi==0.115.0
uvicorn==0.32.0
pydantic==2.10.0
pydantic-settings==2.6.0
python-dotenv==1.0.1
neo4j==5.26.0
pandas==2.2.0
numpy>=1.23.2,<2
scikit-learn==1.5.0
networkx==3.4
spacy==3.8.0
transformers==4.46.0
python-multipart==0.0.9
httpx==0.28.0
redis==5.2.0
celery==5.4.0
flower==2.0.1
prometheus-client==0.20.0
structlog==25.1.0
python-json-logger==2.0.7
pytest==8.3.0
pytest-asyncio==0.24.0
Faker==40.39.0
python-louvain==0.16

## 🚦 Quick Start
# Criminal Network Intelligence Platform - Backend

FastAPI-based backend for criminal network analysis with Neo4j graph database, ML-powered analytics, and multi-source document ingestion.

## Quick Start

### Prerequisites
- Python 3.11 (managed via `uv`)
- Neo4j Community Edition 5.x
- Valkey/Redis 7.x

### Installation (One-time)
```bash
# Create Python 3.11 virtual environment
uv venv --python 3.11 ../venv
source ../venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_lg

# Start services
sudo systemctl start neo4j valkey

# Configure Neo4j (first run only)
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'neo4j'))
with driver.session() as session:
    session.run('ALTER USER neo4j SET PASSWORD \"secretpassword\"')
driver.close()
"

# Generate synthetic data
PYTHONPATH=. python scripts/generate_synthetic_data.py 100 20 150 120 500 1000 --clear
```

### Running the API
```bash
cd ~/criminal-network-platform/backend
source ../venv/bin/activate
PYTHONPATH=. python -m app.main
```
- **API Base**: http://localhost:8000/api/v1
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Running Tests
```bash
cd ~/criminal-network-platform
source venv/bin/activate
python scripts/test_api.py
```

---

## API Structure

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints

#### Health & System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check (Neo4j connectivity) |

#### Network Graph
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/network` | Full network graph (nodes + links) |
| Query Params | `min_weight` (float, default 0.1), `limit` (int, default 1000) | Filter edges by weight, limit results |

**Response**: `GraphData` - `{ nodes: GraphNode[], links: GraphLink[] }`

#### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/risk-scores` | Composite risk scores for all entities |
| GET | `/analytics/centrality` | Centrality measures (PageRank, Betweenness, Closeness, Eigenvector, Degree) |
| GET | `/analytics/communities` | Louvain community detection |
| GET | `/analytics/anomalies` | Structural + temporal anomalies |
| GET | `/analytics/stats` | Network statistics |
| POST | `/analytics/run-full-analysis` | Trigger complete analysis pipeline |

**Query Params for Analytics**:
- `min_weight` (float): Minimum edge weight
- `resolution` (float, communities): Louvain resolution parameter
- `centrality_weight`, `anomaly_weight`, `betweenness_weight` (risk-scores): Scoring weights

#### Entity Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/entities` | Search/filter entities |
| Query Params | `q` (str): Search query, `entity_types` (list), `limit` (int), `offset` (int) | Filtering |

**Response**: `SearchResult` - `{ entities: Entity[], total: int, limit: int, offset: int }`

#### Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/alerts` | Get generated alerts |
| Query Params | `limit` (int), `offset` (int) | Pagination |

#### Document Ingestion
| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| POST | `/ingest/fir` | Ingest FIR (First Information Report) | `IngestFIRRequest` |
| POST | `/ingest/cdr` | Ingest Call Detail Records | `IngestCDRRequest` |
| POST | `/ingest/financial` | Ingest Financial Transactions | `IngestFinancialRequest` |
| POST | `/ingest/surveillance` | Ingest Surveillance Logs | `IngestSurveillanceRequest` |

---

## Data Models

### Entity Types
```
Person, Organization, Location, PhoneNumber, Email, BankAccount,
Vehicle, SocialHandle, Event, Document, CryptoWallet, Other
```

### Relationship Types
```
OWNS, CONTACTED, TRANSFERRED_TO, ASSOCIATED_WITH, LOCATED_AT,
PARTICIPATED_IN, MEMBER_OF, ALIAS_OF, RELATED_TO, SUSPICIOUS_LINK,
EMPLOYED_BY, DIRECTOR_OF, COMMAND_CONTROL
```

### Key Models

#### GraphNode
```json
{
  "id": "uuid",
  "label": "string",
  "entity_type": "Person",
  "properties": {},
  "risk_score": 75.5,
  "size": 25.0
}
```

#### GraphLink
```json
{
  "source": "uuid",
  "target": "uuid",
  "relationship_type": "OWNS",
  "weight": 1.0,
  "properties": { "since": "2024-01-15" }
}
```

#### RiskScore
```json
{
  "entity_id": "uuid",
  "entity_name": "string",
  "risk_score": 85.2,
  "risk_level": "HIGH",
  "contributing_factors": {
    "centrality": 0.8,
    "anomalies": 0.9,
    "betweenness": 0.3
  }
}
```

#### Anomaly
```json
{
  "entity_id": "uuid",
  "entity_name": "string",
  "anomaly_type": "structural_outlier",
  "score": 3.5,
  "description": "Unusual CONTACTED weight...",
  "evidence": ["Edge weight: 12.5", "Z-score: 4.2"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Entity (Search Result)
```json
{
  "id": "uuid",
  "name": "string",
  "entity_type": "Person",
  "properties": {},
  "source_documents": ["doc1", "doc2"],
  "confidence": 0.95,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "risk_score": 75.5,
  "centrality_scores": { "pagerank": 0.05, "betweenness": 0.02, ... }
}
```

---

## Ingestion Request Examples

### FIR Ingestion
```bash
curl -X POST http://localhost:8000/api/v1/ingest/fir \
  -H "Content-Type: application/json" \
  -d '{
    "content": "FIR No. 123/2024... Accused Rahul Sharma...",
    "document_id": "fir_001",
    "source": "police_station_12"
  }'
```

### CDR Ingestion
```bash
curl -X POST http://localhost:8000/api/v1/ingest/cdr \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {
        "caller": "+91-9876543210",
        "receiver": "+91-9123456789",
        "duration": 120,
        "timestamp": "2024-01-15T10:30:00",
        "call_type": "voice",
        "cell_tower": "TWR-001",
        "source_file": "cdr_jan_2024.csv"
      }
    ],
    "source_file": "cdr_jan_2024.csv"
  }'
```

### Financial Ingestion
```bash
curl -X POST http://localhost:8000/api/v1/ingest/financial \
  -H "Content-Type: application/json" \
  -d '{
    "transactions": [
      {
        "sender_account": "ACC001",
        "receiver_account": "ACC002",
        "amount": 500000,
        "currency": "INR",
        "timestamp": "2024-01-15T11:00:00",
        "transaction_type": "transfer",
        "reference": "TXN123456",
        "source_file": "bank_statements.csv"
      }
    ],
    "source_file": "bank_statements.csv"
  }'
```

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── core/
│   │   └── config.py           # Configuration (Neo4j, Redis, etc.)
│   ├── db/
│   │   └── neo4j.py            # Neo4j driver wrapper
│   ├── api/
│   │   └── routes.py           # All REST endpoints
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   └── services/
│       ├── ml_engine.py        # Graph analytics (centrality, communities, anomalies, risk)
│       ├── graph_builder.py    # Graph construction from ingested data
│       └── nlp_extractor.py    # spaCy NER for document processing
├── scripts/
│   ├── generate_synthetic_data.py  # Synthetic data generator
│   └── process_documents.py        # Batch document processing
├── requirements.txt
└── README.md
```

---

## Configuration

Environment variables (`.env` file in backend/):
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=secretpassword
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
```

---

## Architecture Notes

- **Graph Storage**: Neo4j (nodes=entities, edges=relationships)
- **Caching**: Valkey/Redis for query results
- **NLP**: spaCy `en_core_web_lg` + custom entity ruler for Indian names, orgs, locations
- **ML**: NetworkX for graph algorithms, scikit-learn for anomaly detection
- **No Docker**: All services run natively via systemd

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: app` | Run from `backend/` with `PYTHONPATH=.` |
| Neo4j connection refused | `sudo systemctl start neo4j` |
| `Address already in use` (port 8000) | `pkill -f "python -m app.main"` |
| Pydantic validation errors | Check entity/relationship types match enums in `schemas.py` |
| APOC errors | Ensure plugin installed at `/usr/share/neo4j/plugins/apoc-5.15.0-core.jar` |
## 📚 Documentation

- [Architecture Decision Records](docs/adr/)
- [API Specification](docs/api/openapi.yaml)
- [Data Schema Reference](docs/schemas/)
- [Deployment Guide](docs/deployment/)
- [User Manual](docs/user-guide/)
- [Developer Guide](docs/developer-guide/)

## 🔐 Security Considerations

- Role-based access control (RBAC)
- Audit logging for all data access
- Encryption at rest (Neo4j) and in transit (TLS)
- Input validation and sanitization
- Rate limiting and DDoS protection
- Secure secrets management (HashiCorp Vault / AWS Secrets Manager)

## 🚀 Production Deployment

### Kubernetes
```bash
kubectl apply -f k8s/
```

### Docker Swarm
```bash
docker stack deploy -c docker-compose.swarm.yml cnip
```

### Monitoring Stack
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- SIH 2026 Problem Statement PS26189
- Neo4j Graph Database
- spaCy NLP Library
- React Force Graph
- NetworkX & PyTorch Geometric Communities

---

**Built for Law Enforcement & Intelligence Agencies** | **Project PS26189**
