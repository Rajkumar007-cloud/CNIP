from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EntityType(str, Enum):
    PERSON = "Person"
    ORGANIZATION = "Organization"
    LOCATION = "Location"
    PHONE_NUMBER = "PhoneNumber"
    EMAIL = "Email"
    BANK_ACCOUNT = "BankAccount"
    VEHICLE = "Vehicle"
    SOCIAL_HANDLE = "SocialHandle"
    EVENT = "Event"
    DOCUMENT = "Document"
    CRYPTO_WALLET = "CryptoWallet"
    OTHER = "Other"


class RelationshipType(str, Enum):
    OWNS = "OWNS"
    CONTACTED = "CONTACTED"
    TRANSFERRED_TO = "TRANSFERRED_TO"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    LOCATED_AT = "LOCATED_AT"
    PARTICIPATED_IN = "PARTICIPATED_IN"
    MEMBER_OF = "MEMBER_OF"
    ALIAS_OF = "ALIAS_OF"
    RELATED_TO = "RELATED_TO"
    SUSPICIOUS_LINK = "SUSPICIOUS_LINK"
    EMPLOYED_BY = "EMPLOYED_BY"
    DIRECTOR_OF = "DIRECTOR_OF"
    COMMAND_CONTROL = "COMMAND_CONTROL"


class EntityBase(BaseModel):
    name: str
    entity_type: EntityType
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_documents: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class EntityCreate(EntityBase):
    pass


class EntityUpdate(BaseModel):
    name: Optional[str] = None
    entity_type: Optional[EntityType] = None
    properties: Optional[Dict[str, Any]] = None
    source_documents: Optional[List[str]] = None
    confidence: Optional[float] = None


class Entity(EntityBase):
    id: str
    created_at: datetime
    updated_at: datetime
    risk_score: Optional[float] = None
    centrality_scores: Optional[Dict[str, float]] = None

    class Config:
        from_attributes = True


class RelationshipBase(BaseModel):
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(default=1.0, ge=0.0)
    source_documents: List[str] = Field(default_factory=list)


class RelationshipCreate(RelationshipBase):
    pass


class Relationship(RelationshipBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class GraphNode(BaseModel):
    id: str
    label: str
    entity_type: EntityType
    properties: Dict[str, Any] = Field(default_factory=dict)
    risk_score: Optional[float] = None
    size: float = Field(default=10.0)


class GraphLink(BaseModel):
    source: str
    target: str
    relationship_type: RelationshipType
    weight: float = Field(default=1.0)
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphData(BaseModel):
    nodes: List[GraphNode]
    links: List[GraphLink]


class RiskScore(BaseModel):
    entity_id: str
    entity_name: str
    entity_type: EntityType
    risk_score: float
    network_influence: float
    anomaly_score: float
    factors: Dict[str, float]
    rank: int


class CentralityScores(BaseModel):
    entity_id: str
    entity_name: str
    pagerank: float
    betweenness: float
    closeness: float
    eigenvector: float
    degree: int


class Community(BaseModel):
    community_id: int
    members: List[str]
    size: int
    modularity: float
    key_entities: List[str]


class Anomaly(BaseModel):
    entity_id: str
    entity_name: str
    anomaly_type: str
    score: float
    description: str
    evidence: List[str]
    timestamp: datetime


class Alert(BaseModel):
    id: str
    alert_type: str
    severity: str
    title: str
    description: str
    entities_involved: List[str]
    evidence: List[str]
    created_at: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class IngestFIRRequest(BaseModel):
    content: str
    document_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IngestCDRRequest(BaseModel):
    records: List[Dict[str, Any]]
    source_file: str


class IngestFinancialRequest(BaseModel):
    transactions: List[Dict[str, Any]]
    source_file: str


class IngestSurveillanceRequest(BaseModel):
    reports: List[Dict[str, Any]]
    source_file: str


class SearchRequest(BaseModel):
    query: str
    entity_types: Optional[List[EntityType]] = None
    limit: int = Field(default=50, le=500)
    offset: int = Field(default=0, ge=0)
    filters: Dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    entities: List[Entity]
    total: int
    limit: int
    offset: int


class PathRequest(BaseModel):
    source_id: str
    target_id: str
    max_depth: int = Field(default=6, le=10)


class PathResult(BaseModel):
    path: List[Dict[str, Any]]
    length: int
    total_weight: float


class NetworkStats(BaseModel):
    total_entities: int
    total_relationships: int
    entity_types: Dict[str, int]
    relationship_types: Dict[str, int]
    communities: int
    avg_risk_score: float