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

## 🚦 Quick Start

### Prerequisites
- Docker & Docker Compose
- 16GB+ RAM recommended
- 50GB+ disk space

### 1. Clone and Configure
```bash
cd criminal-network-platform
cp .env.example .env
# Edit .env with your configuration
```

### 2. Start the Platform
```bash
# Start all services
docker-compose up -d

# Or start with data initialization
docker-compose --profile init up -d
```

### 3. Access the Platform
- **Frontend Dashboard**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474

### 4. Initialize Sample Data
```bash
# Generate synthetic criminal network data
docker-compose run --rm data-generator

# Or run NLP extraction on FIR reports
docker-compose run --rm nlp-processor
```

## 📊 Key Features

### 1. Multi-Source Data Ingestion
- **FIR Reports** (PDF, Text, DOCX) → NLP Entity Extraction
- **CDR Files** (CSV, Excel) → Call network construction
- **Financial Records** → Transaction graph building
- **Surveillance Reports** → Location-time entity linking
- **Social Media** → OSINT entity resolution
- **Criminal History** → Prior record integration

### 2. Entity Extraction (NLP)
- **People**: Names, aliases, roles
- **Organizations**: Gangs, companies, shell companies
- **Locations**: Addresses, GPS coordinates, landmarks
- **Communication**: Phone numbers, emails, social handles
- **Financial**: Bank accounts, crypto wallets, transaction IDs
- **Vehicles**: License plates, VINs, vehicle descriptions
- **Events**: Crimes, meetings, transactions, arrests

### 3. Graph Analytics
- **Centrality Measures**: PageRank, Betweenness, Closeness, Eigenvector
- **Community Detection**: Louvain, Label Propagation, Infomap
- **Link Prediction**: Adamic-Adar, Jaccard, Preferential Attachment
- **Subgraph Analysis**: Cliques, Motifs, Ego Networks
- **Temporal Analysis**: Dynamic networks, Evolution patterns

### 4. ML-Powered Detection
- **Anomaly Detection**: Isolation Forest, Local Outlier Factor, Graph Autoencoders
- **Risk Scoring**: Multi-factor composite risk scores
- **Pattern Recognition**: Structuring, Layering, Smurfing, Round-tripping
- **Influence Analysis**: Key player identification, Network disruption simulation

### 5. Investigator Dashboard
- **Network Visualization**: Interactive force-directed graphs (2D/3D)
- **Timeline View**: Temporal event sequences
- **Geospatial Map**: Entity locations and movements
- **Risk Priority List**: Ranked suspects with evidence trails
- **Alert Center**: Real-time suspicious activity notifications
- **Report Generation**: Evidence packages, Network summaries

## 🔧 Configuration

Key environment variables (`.env`):

```env
# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password

# Backend
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your_secret_key
ALLOWED_ORIGINS=http://localhost:5173

# NLP
SPACY_MODEL=en_core_web_lg
TRANSFORMERS_MODEL=bert-base-uncased

# ML
ANOMALY_CONTAMINATION=0.05
RISK_SCORE_WEIGHTS='{"pagerank": 0.4, "betweenness": 0.2, "anomaly": 0.4}'

# Frontend
VITE_API_BASE=http://localhost:8000
VITE_WS_BASE=ws://localhost:8000
```

## 📈 API Endpoints

### Network Graph
- `GET /api/v1/network` - Full network graph
- `GET /api/v1/network/{entity_id}` - Ego network
- `GET /api/v1/network/path/{source}/{target}` - Shortest path

### Analytics
- `GET /api/v1/analytics/centrality` - Centrality scores
- `GET /api/v1/analytics/communities` - Community detection
- `GET /api/v1/analytics/anomalies` - Detected anomalies
- `GET /api/v1/analytics/risk-scores` - Entity risk scores

### Entities
- `GET /api/v1/entities` - List entities (paginated, filterable)
- `GET /api/v1/entities/{id}` - Entity details with relationships
- `POST /api/v1/entities/search` - Advanced entity search

### Ingestion
- `POST /api/v1/ingest/fir` - Upload FIR document
- `POST /api/v1/ingest/cdr` - Upload CDR file
- `POST /api/v1/ingest/financial` - Upload financial records
- `POST /api/v1/ingest/surveillance` - Upload surveillance report

### Alerts
- `GET /api/v1/alerts` - Active alerts
- `GET /api/v1/alerts/{id}` - Alert details
- `POST /api/v1/alerts/{id}/acknowledge` - Acknowledge alert

## 🧪 Testing

```bash
# Backend tests
cd backend && pytest -v

# Frontend tests
cd frontend && npm test

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

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