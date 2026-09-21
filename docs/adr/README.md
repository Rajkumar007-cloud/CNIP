# Criminal Network Intelligence Platform (CNIP)
## Architecture Decision Records

### ADR-001: Graph Database Selection
**Status:** Accepted  
**Date:** 2024-01-15  
**Decision:** Use Neo4j as the primary graph database  
**Rationale:** Native graph storage, Cypher query language, APOC plugins, Graph Data Science library, proven at scale for fraud detection and network analysis.

### ADR-002: Backend Framework
**Status:** Accepted  
**Date:** 2024-01-15  
**Decision:** Use FastAPI for the REST API  
**Rationale:** High performance (async), automatic OpenAPI docs, Pydantic validation, type hints, growing ecosystem, excellent for ML model serving.

### ADR-003: Frontend Framework
**Status:** Accepted  
**Date:** 2024-01-15  
**Decision:** Use React 18 with TypeScript and Vite  
**Rationale:** Component-based architecture, strong typing, fast HMR, excellent graph visualization libraries (react-force-graph), large talent pool.

### ADR-004: NLP Pipeline
**Status:** Accepted  
**Date:** 2024-01-15  
**Decision:** Use spaCy with custom entity ruler + transformer models  
**Rationale:** Fast inference, customizable NER, rule-based patterns for domain-specific entities (Indian phone, PAN, Aadhaar, IFSC), production-ready.

### ADR-005: ML/Analytics Engine
**Status:** Accepted  
**Date:** 2024-01-15  
**Decision:** NetworkX + scikit-learn + PyTorch Geometric  
**Rationale:** NetworkX for graph algorithms, scikit-learn for traditional ML (Isolation Forest), PyG for future GNN extensions, all Python-native.

### ADR-006: Container Orchestration
**Status:** Accepted  
**Date:** 2024-01-15  
**Decision:** Docker Compose for development, Kubernetes for production  
**Rationale:** Simple local development, production-ready with K8s manifests, supports all services (Neo4j, Redis, Backend, Frontend, Celery, Monitoring).

### ADR-007: Message Queue
**Status:** Accepted  
**Date:** 2024-01-15  
**Decision:** Redis + Celery for async task processing  
**Rationale:** Simple setup, supports scheduled tasks (Celery Beat), monitoring (Flower), scales horizontally, integrates with FastAPI.

### ADR-008: Monitoring Stack
**Status:** Accepted  
**Date:** 2024-01-15  
**Decision:** Prometheus + Grafana  
**Rationale:** Industry standard, excellent Neo4j/Redis/FastAPI exporters, custom dashboards for network metrics, alerting built-in.

### ADR-009: Data Ingestion Patterns
**Status:** Accepted  
**Date:** 2024-01-15  
**Decision:** Dual-path ingestion (API for real-time, batch scripts for bulk)  
**Rationale:** API for interactive uploads, scripts for large historical data, both use same graph builder service.

### ADR-010: Risk Scoring Methodology
**Status:** Accepted  
**Date:** 2024-01-15  
**Decision:** Composite score: 40% PageRank + 20% Betweenness + 40% Anomaly  
**Rationale:** PageRank identifies influential nodes, Betweenness finds bridges, Anomaly catches suspicious behavior, weights tunable per investigation.