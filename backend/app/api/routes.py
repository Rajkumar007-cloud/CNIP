from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from app.models.schemas import (
    GraphData, GraphNode, GraphLink, RiskScore, CentralityScores,
    Community, Anomaly, Alert, SearchRequest, SearchResult,
    PathRequest, PathResult, NetworkStats, Entity, EntityCreate,
    IngestFIRRequest, IngestCDRRequest, IngestFinancialRequest,
    IngestSurveillanceRequest, EntityType, RelationshipType
)
from app.services.graph_builder import GraphBuilder
from app.services.ml_engine import get_ml_engine
from app.services.nlp_extractor import get_extractor
from app.db.neo4j import get_db
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["network"])


@router.get("/network", response_model=GraphData)
async def get_full_network(
    min_weight: float = Query(0.1, ge=0.0, le=10.0),
    limit: int = Query(1000, ge=10, le=5000)
):
    """Get the full network graph for visualization."""
    ml_engine = get_ml_engine()
    ml_engine.analytics.load_graph(min_weight=min_weight)
    
    G = ml_engine.analytics.graph
    
    # Map entity type strings to enum
    entity_type_map = {
        "Person": EntityType.PERSON,
        "Organization": EntityType.ORGANIZATION,
        "Location": EntityType.LOCATION,
        "PhoneNumber": EntityType.PHONE_NUMBER,
        "Email": EntityType.EMAIL,
        "BankAccount": EntityType.BANK_ACCOUNT,
        "Vehicle": EntityType.VEHICLE,
        "SocialHandle": EntityType.SOCIAL_HANDLE,
        "Event": EntityType.EVENT,
        "Document": EntityType.DOCUMENT,
        "CryptoWallet": EntityType.CRYPTO_WALLET,
    }
    
    # Map relationship types to enum
    rel_type_map = {
        "OWNS": RelationshipType.OWNS,
        "CONTACTED": RelationshipType.CONTACTED,
        "TRANSFERRED_TO": RelationshipType.TRANSFERRED_TO,
        "ASSOCIATED_WITH": RelationshipType.ASSOCIATED_WITH,
        "LOCATED_AT": RelationshipType.LOCATED_AT,
        "PARTICIPATED_IN": RelationshipType.PARTICIPATED_IN,
        "MEMBER_OF": RelationshipType.MEMBER_OF,
        "ALIAS_OF": RelationshipType.ALIAS_OF,
        "RELATED_TO": RelationshipType.RELATED_TO,
        "SUSPICIOUS_LINK": RelationshipType.SUSPICIOUS_LINK,
        "EMPLOYED_BY": RelationshipType.EMPLOYED_BY,
        "DIRECTOR_OF": RelationshipType.DIRECTOR_OF,
        "COMMAND_CONTROL": RelationshipType.COMMAND_CONTROL,
    }
    
    nodes = []
    for nid in list(G.nodes())[:limit]:
        et = G.nodes[nid].get("entity_type", "Unknown")
        name = ml_engine.analytics.entity_name_map.get(nid, nid)
        nodes.append(GraphNode(
            id=nid,
            label=name if name else nid,  # Ensure label is never None
            entity_type=entity_type_map.get(et, EntityType.DOCUMENT),
            properties=dict(G.nodes[nid]),
            size=10.0 + G.degree(nid, weight="weight") * 2
        ))
    
    links = []
    for u, v, data in list(G.edges(data=True))[:limit * 2]:
        if u in ml_engine.analytics.entity_id_map and v in ml_engine.analytics.entity_id_map:
            rel = data.get("rel_type", "CONNECTED")
            props = data.get("properties", {})
            if isinstance(props, str):
                import json
                try:
                    props = json.loads(props)
                except:
                    props = {}
            links.append(GraphLink(
                source=u,
                target=v,
                relationship_type=rel_type_map.get(rel, RelationshipType.RELATED_TO),
                weight=data.get("weight", 1.0),
                properties=props
            ))
    
    return GraphData(nodes=nodes, links=links)


@router.get("/network/{entity_id}", response_model=GraphData)
async def get_ego_network(entity_id: str, radius: int = Query(2, ge=1, le=3)):
    """Get ego network for a specific entity."""
    ml_engine = get_ml_engine()
    ego_data = ml_engine.analytics.get_ego_network(entity_id, radius=radius)
    
    nodes = [GraphNode(**n) for n in ego_data["nodes"]]
    links = [GraphLink(**l) for l in ego_data["links"]]
    
    return GraphData(nodes=nodes, links=links)


@router.get("/analytics/centrality", response_model=List[CentralityScores])
async def get_centrality_scores():
    """Get centrality scores for all entities."""
    ml_engine = get_ml_engine()
    return ml_engine.analytics.calculate_centrality()


@router.get("/analytics/communities", response_model=List[Community])
async def get_communities(resolution: float = Query(1.0, ge=0.1, le=5.0)):
    """Get detected communities."""
    ml_engine = get_ml_engine()
    return ml_engine.analytics.detect_communities(resolution=resolution)


@router.get("/analytics/anomalies", response_model=List[Anomaly])
async def get_anomalies(contamination: float = Query(0.05, ge=0.01, le=0.2)):
    """Get detected anomalies."""
    ml_engine = get_ml_engine()
    return ml_engine.analytics.detect_anomalies(contamination=contamination)


@router.get("/analytics/risk-scores", response_model=List[RiskScore])
async def get_risk_scores(
    centrality_weight: float = Query(0.4, ge=0.0, le=1.0),
    anomaly_weight: float = Query(0.4, ge=0.0, le=1.0),
    betweenness_weight: float = Query(0.2, ge=0.0, le=1.0)
):
    """Get risk scores for all entities."""
    ml_engine = get_ml_engine()
    return ml_engine.analytics.calculate_risk_scores(
        centrality_weight=centrality_weight,
        anomaly_weight=anomaly_weight,
        betweenness_weight=betweenness_weight
    )


@router.get("/analytics/stats", response_model=NetworkStats)
async def get_network_stats():
    """Get network statistics."""
    ml_engine = get_ml_engine()
    ml_engine.analytics.load_graph()
    
    G = ml_engine.analytics.graph
    db = get_db()
    
    # Get entity type counts
    entity_types = {}
    cypher = """
    MATCH (n)
    RETURN labels(n)[0] as type, count(*) as count
    """
    results = db.query(cypher)
    for r in results:
        entity_types[r["type"]] = r["count"]
    
    # Get relationship type counts
    rel_types = {}
    cypher = """
    MATCH ()-[r]->()
    RETURN type(r) as type, count(*) as count
    """
    results = db.query(cypher)
    for r in results:
        rel_types[r["type"]] = r["count"]
    
    # Risk scores for avg
    risk_scores = ml_engine.analytics.calculate_risk_scores()
    avg_risk = sum(r.risk_score for r in risk_scores) / len(risk_scores) if risk_scores else 0
    
    communities = ml_engine.analytics.detect_communities()
    
    return NetworkStats(
        total_entities=G.number_of_nodes(),
        total_relationships=G.number_of_edges(),
        entity_types=entity_types,
        relationship_types=rel_types,
        communities=len(communities),
        avg_risk_score=avg_risk
    )


@router.get("/entities", response_model=SearchResult)
async def search_entities(
    q: str = Query("", description="Search query"),
    entity_types: Optional[List[str]] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Search entities by name or properties."""
    db = get_db()
    
    # Build dynamic query
    where_clauses = []
    params = {"limit": limit, "offset": offset}
    
    if q:
        where_clauses.append("(n.name CONTAINS $query OR any(k IN keys(n.properties_json) WHERE n.properties_json[k] CONTAINS $query))")
        params["query"] = q
    
    if entity_types and len(entity_types) > 0:
        type_conditions = " OR ".join([f"'{t}' IN labels(n)" for t in entity_types])
        where_clauses.append(f"({type_conditions})")
    
    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    # Count total
    count_cypher = f"MATCH (n) {where_clause} RETURN count(n) as total"
    count_result = db.query(count_cypher, params)
    total = count_result[0]["total"] if count_result else 0
    
    # Get entities
    cypher = f"""
    MATCH (n) {where_clause}
    RETURN n.id as id, n.name as name, labels(n)[0] as entity_type,
           n.properties_json as properties, n.source_documents as source_documents,
           n.confidence as confidence, n.created_at as created_at,
           n.updated_at as updated_at, n.risk_score as risk_score,
           n.centrality_scores as centrality_scores
    SKIP $offset LIMIT $limit
    """
    
    results = db.query(cypher, params)
    
    entities = []
    for r in results:
        # Parse properties JSON if it's a string
        props = r["properties"]
        if isinstance(props, str):
            import json
            try:
                props = json.loads(props)
            except:
                props = {}
        
        # Handle Neo4j DateTime
        from datetime import datetime
        created_at = r["created_at"]
        if hasattr(created_at, 'to_native'):
            created_at = created_at.to_native()
        elif created_at is None:
            created_at = datetime.utcnow()
            
        updated_at = r["updated_at"]
        if hasattr(updated_at, 'to_native'):
            updated_at = updated_at.to_native()
        elif updated_at is None:
            updated_at = datetime.utcnow()
        
        entities.append(Entity(
            id=r["id"],
            name=r["name"] or r["id"],  # Fallback to id if name is None
            entity_type=r["entity_type"],
            properties=props or {},
            source_documents=r["source_documents"] or [],
            confidence=r["confidence"] or 1.0,
            created_at=created_at,
            updated_at=updated_at,
            risk_score=r["risk_score"],
            centrality_scores=r["centrality_scores"]
        ))
    
    return SearchResult(entities=entities, total=total, limit=limit, offset=offset)


@router.get("/entities/{entity_id}", response_model=Entity)
async def get_entity(entity_id: str):
    """Get entity by ID with full details."""
    db = get_db()
    
    cypher = """
    MATCH (n {id: $id})
    RETURN n.id as id, n.name as name, labels(n)[0] as entity_type,
           n.properties_json as properties, n.source_documents as source_documents,
           n.confidence as confidence, n.created_at as created_at,
           n.updated_at as updated_at, n.risk_score as risk_score,
           n.centrality_scores as centrality_scores
    """
    
    results = db.query(cypher, {"id": entity_id})
    
    if not results:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    r = results[0]
    return Entity(
        id=r["id"],
        name=r["name"],
        entity_type=r["entity_type"],
        properties=r["properties"] or {},
        source_documents=r["source_documents"] or [],
        confidence=r["confidence"] or 1.0,
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        risk_score=r["risk_score"],
        centrality_scores=r["centrality_scores"]
    )


@router.post("/entities/{entity_id}/profile")
async def get_entity_profile(entity_id: str):
    """Get comprehensive profile for an entity."""
    ml_engine = get_ml_engine()
    return ml_engine.get_entity_profile(entity_id)


@router.post("/network/path", response_model=PathResult)
async def find_path(request: PathRequest):
    """Find shortest path between two entities."""
    ml_engine = get_ml_engine()
    path = ml_engine.analytics.find_shortest_path(
        request.source_id, request.target_id, request.max_depth
    )
    
    if path is None:
        raise HTTPException(status_code=404, detail="No path found within max depth")
    
    total_weight = sum(p["weight"] for p in path)
    
    return PathResult(
        path=path,
        length=len(path),
        total_weight=total_weight
    )


# Ingestion endpoints
@router.post("/ingest/fir")
async def ingest_fir(request: IngestFIRRequest):
    """Ingest FIR document and extract entities."""
    extractor = get_extractor()
    builder = GraphBuilder()
    
    # Extract entities
    entities = extractor.extract_entities(request.content, request.document_id or "fir_upload")
    
    # Build graph nodes
    entity_map = builder.build_from_entities(entities)
    
    # Add graph IDs to entities
    for ent in entities:
        ent["graph_id"] = entity_map.get(ent["text"].lower().strip())
    
    # Create co-occurrence relationships
    builder.link_entities_cooccurrence(entities)
    
    return {
        "status": "success",
        "entities_extracted": len(entities),
        "entities_created": len(entity_map),
        "document_id": request.document_id
    }


@router.post("/ingest/cdr")
async def ingest_cdr(request: IngestCDRRequest):
    """Ingest CDR records."""
    builder = GraphBuilder()
    count = builder.build_cdr_relationships(request.records)
    
    return {
        "status": "success",
        "relationships_created": count,
        "source_file": request.source_file
    }


@router.post("/ingest/financial")
async def ingest_financial(request: IngestFinancialRequest):
    """Ingest financial transaction records."""
    builder = GraphBuilder()
    count = builder.build_financial_relationships(request.transactions)
    
    return {
        "status": "success",
        "relationships_created": count,
        "source_file": request.source_file
    }


@router.post("/ingest/surveillance")
async def ingest_surveillance(request: IngestSurveillanceRequest):
    """Ingest surveillance reports."""
    extractor = get_extractor()
    builder = GraphBuilder()
    
    all_entities = []
    
    for report in request.reports:
        content = report.get("content", "")
        doc_id = report.get("id", request.source_file)
        
        entities = extractor.extract_entities(content, doc_id)
        all_entities.extend(entities)
    
    entity_map = builder.build_from_entities(all_entities)
    
    for ent in all_entities:
        ent["graph_id"] = entity_map.get(ent["text"].lower().strip())
    
    builder.link_entities_cooccurrence(all_entities)
    
    return {
        "status": "success",
        "entities_extracted": len(all_entities),
        "entities_created": len(entity_map),
        "reports_processed": len(request.reports)
    }


@router.post("/analysis/run")
async def run_full_analysis():
    """Trigger full network analysis."""
    ml_engine = get_ml_engine()
    result = ml_engine.run_full_analysis()
    return {"status": "success", "result": result}


@router.get("/alerts", response_model=List[Alert])
async def get_alerts(
    severity: Optional[str] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """Get active alerts."""
    # This would typically query an alerts table/collection
    # For now, generate alerts from anomalies
    ml_engine = get_ml_engine()
    anomalies = ml_engine.analytics.detect_anomalies()
    
    alerts = []
    for i, anomaly in enumerate(anomalies[:limit]):
        severity_level = "high" if anomaly.score > 0.8 else "medium" if anomaly.score > 0.5 else "low"
        
        if severity and severity_level != severity:
            continue
        
        alerts.append(Alert(
            id=f"alert_{anomaly.entity_id}",
            alert_type=anomaly.anomaly_type,
            severity=severity_level,
            title=f"{anomaly.anomaly_type.replace('_', ' ').title()} Detected",
            description=anomaly.description,
            entities_involved=[anomaly.entity_id],
            evidence=anomaly.evidence,
            created_at=anomaly.timestamp,
            acknowledged=False
        ))
    
    return alerts


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, acknowledged_by: str):
    """Acknowledge an alert."""
    # In production, update the alert in database
    return {"status": "success", "alert_id": alert_id, "acknowledged_by": acknowledged_by}