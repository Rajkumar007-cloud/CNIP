from typing import List, Dict, Any, Optional, Set, Tuple
from app.db.neo4j import get_db
from app.models.schemas import EntityType, RelationshipType
import structlog
import uuid
from datetime import datetime

logger = structlog.get_logger()


class GraphBuilder:
    def __init__(self):
        self.db = get_db()
    
    def create_entity(self, entity_data: Dict[str, Any]) -> str:
        """Create or merge an entity node in the graph."""
        entity_id = entity_data.get("id") or str(uuid.uuid4())
        name = entity_data["name"]
        entity_type = entity_data["entity_type"]
        properties = entity_data.get("properties", {})
        source_documents = entity_data.get("source_documents", [])
        confidence = entity_data.get("confidence", 1.0)
        
        # Build dynamic labels
        labels = f":{entity_type}"
        
        cypher = f"""
        MERGE (e{labels} {{id: $id}})
        ON CREATE SET
            e.name = $name,
            e.created_at = datetime(),
            e.confidence = $confidence,
            e.source_documents = $source_documents,
            e.properties_json = $properties
        ON MATCH SET
            e.name = $name,
            e.updated_at = datetime(),
            e.confidence = CASE WHEN $confidence > e.confidence THEN $confidence ELSE e.confidence END,
            e.source_documents = CASE 
                WHEN e.source_documents IS NULL THEN $source_documents
                ELSE [x IN $source_documents WHERE NOT x IN e.source_documents | x] + e.source_documents
            END,
            e.properties_json = $properties
        RETURN e.id as id
        """
        
        result = self.db.query(cypher, {
            "id": entity_id,
            "name": name,
            "confidence": confidence,
            "source_documents": source_documents,
            "properties": json.dumps(properties)
        })
        
        return result[0]["id"] if result else entity_id
    
    def create_relationship(self, rel_data: Dict[str, Any]) -> str:
        """Create a relationship between two entities."""
        source_id = rel_data["source_id"]
        target_id = rel_data["target_id"]
        rel_type = rel_data["relationship_type"]
        properties = rel_data.get("properties", {})
        weight = rel_data.get("weight", 1.0)
        source_documents = rel_data.get("source_documents", [])
        
        cypher = f"""
        MATCH (source {{id: $source_id}})
        MATCH (target {{id: $target_id}})
        MERGE (source)-[r:{rel_type}]->(target)
        ON CREATE SET
            r.id = $rel_id,
            r.created_at = datetime(),
            r.weight = $weight,
            r.properties_json = $properties,
            r.source_documents = $source_documents
        ON MATCH SET
            r.weight = $weight,
            r.properties_json = $properties,
            r.source_documents = CASE 
                WHEN r.source_documents IS NULL THEN $source_documents
                ELSE [x IN $source_documents WHERE NOT x IN r.source_documents | x] + r.source_documents
            END
        RETURN r.id as id
        """
        
        rel_id = str(uuid.uuid4())
        result = self.db.query(cypher, {
            "source_id": source_id,
            "target_id": target_id,
            "rel_id": rel_id,
            "weight": weight,
            "properties": json.dumps(properties),
            "source_documents": source_documents
        })
        
        return result[0]["id"] if result else rel_id
    
    def build_from_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, str]:
        """Build graph nodes from extracted entities. Returns mapping of entity text to node ID."""
        entity_id_map = {}
        
        for entity in entities:
            entity_id = self.create_entity({
                "name": entity["text"],
                "entity_type": entity["entity_type"],
                "properties": {
                    "original_label": entity.get("label", ""),
                    "confidence": entity.get("confidence", 0.9)
                },
                "source_documents": [entity.get("source_document", ""), entity.get("document_id", "")],
                "confidence": entity.get("confidence", 0.9)
            })
            entity_id_map[entity["text"].lower().strip()] = entity_id
        
        logger.info("entities_created", count=len(entity_id_map))
        return entity_id_map
    
    def build_cdr_relationships(self, cdr_records: List[Dict[str, Any]]) -> int:
        """Build CALL relationships from CDR data."""
        count = 0
        
        for record in cdr_records:
            caller = record.get("caller") or record.get("source") or record.get("calling_number")
            receiver = record.get("receiver") or record.get("target") or record.get("called_number")
            
            if not caller or not receiver:
                continue
            
            # Create or get phone number entities
            caller_id = self._get_or_create_phone(caller)
            receiver_id = self._get_or_create_phone(receiver)
            
            # Create CALL relationship
            properties = {
                "duration": record.get("duration", 0),
                "timestamp": record.get("timestamp") or record.get("date_time"),
                "cell_tower": record.get("cell_tower") or record.get("tower_id"),
                "call_type": record.get("call_type", "voice")
            }
            
            self.create_relationship({
                "source_id": caller_id,
                "target_id": receiver_id,
                "relationship_type": RelationshipType.CONTACTED.value,
                "properties": properties,
                "weight": 1.0,
                "source_documents": [record.get("source_file", "cdr_import")]
            })
            count += 1
        
        logger.info("cdr_relationships_created", count=count)
        return count
    
    def _get_or_create_phone(self, phone: str) -> str:
        """Get existing phone node or create new one."""
        # Clean phone number
        clean_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
        
        cypher = """
        MERGE (p:PhoneNumber {number: $number})
        ON CREATE SET
            p.id = $id,
            p.created_at = datetime(),
            p.formatted = $formatted
        RETURN p.id as id
        """
        
        result = self.db.query(cypher, {
            "number": clean_phone,
            "id": str(uuid.uuid4()),
            "formatted": phone
        })
        
        return result[0]["id"] if result else str(uuid.uuid4())
    
    def build_financial_relationships(self, transactions: List[Dict[str, Any]]) -> int:
        """Build TRANSFERRED_TO relationships from financial data."""
        count = 0
        
        for txn in transactions:
            sender = txn.get("sender") or txn.get("from_account") or txn.get("origin")
            receiver = txn.get("receiver") or txn.get("to_account") or txn.get("destination")
            amount = txn.get("amount", 0)
            
            if not sender or not receiver:
                continue
            
            sender_id = self._get_or_create_account(sender)
            receiver_id = self._get_or_create_account(receiver)
            
            properties = {
                "amount": float(amount),
                "currency": txn.get("currency", "INR"),
                "timestamp": txn.get("timestamp") or txn.get("date"),
                "transaction_type": txn.get("type", "transfer"),
                "reference": txn.get("reference", "")
            }
            
            self.create_relationship({
                "source_id": sender_id,
                "target_id": receiver_id,
                "relationship_type": RelationshipType.TRANSFERRED_TO.value,
                "properties": properties,
                "weight": min(float(amount) / 100000, 10.0),  # Normalize weight
                "source_documents": [txn.get("source_file", "financial_import")]
            })
            count += 1
        
        logger.info("financial_relationships_created", count=count)
        return count
    
    def _get_or_create_account(self, account: str) -> str:
        """Get existing account node or create new one."""
        clean_account = re.sub(r'[\s\-]', '', account)
        
        cypher = """
        MERGE (a:BankAccount {account_no: $account_no})
        ON CREATE SET
            a.id = $id,
            a.created_at = datetime()
        RETURN a.id as id
        """
        
        result = self.db.query(cypher, {
            "account_no": clean_account,
            "id": str(uuid.uuid4())
        })
        
        return result[0]["id"] if result else str(uuid.uuid4())
    
    def link_entity_to_phone(self, entity_name: str, phone: str) -> bool:
        """Link a person/organization to a phone number."""
        clean_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
        
        cypher = """
        MATCH (e {name: $name})
        MATCH (p:PhoneNumber {number: $phone})
        MERGE (e)-[r:OWNS]->(p)
        RETURN r
        """
        
        result = self.db.query(cypher, {"name": entity_name, "phone": clean_phone})
        return len(result) > 0
    
    def link_entity_to_account(self, entity_name: str, account: str) -> bool:
        """Link a person/organization to a bank account."""
        clean_account = re.sub(r'[\s\-]', '', account)
        
        cypher = """
        MATCH (e {name: $name})
        MATCH (a:BankAccount {account_no: $account})
        MERGE (e)-[r:OWNS]->(a)
        RETURN r
        """
        
        result = self.db.query(cypher, {"name": entity_name, "account": clean_account})
        return len(result) > 0
    
    def link_entities_cooccurrence(self, entities: List[Dict[str, Any]], window: int = 5) -> int:
        """Create ASSOCIATED_WITH relationships between entities that co-occur in documents."""
        count = 0
        doc_entities = {}
        
        # Group entities by document
        for ent in entities:
            doc_id = ent.get("document_id", ent.get("source_document", "unknown"))
            if doc_id not in doc_entities:
                doc_entities[doc_id] = []
            doc_entities[doc_id].append(ent)
        
        # Create co-occurrence relationships within each document
        for doc_id, ents in doc_entities.items():
            for i, ent1 in enumerate(ents):
                for ent2 in ents[i+1:i+window+1]:
                    id1 = ent1.get("graph_id")
                    id2 = ent2.get("graph_id")
                    
                    if id1 and id2 and id1 != id2:
                        self.create_relationship({
                            "source_id": id1,
                            "target_id": id2,
                            "relationship_type": RelationshipType.ASSOCIATED_WITH.value,
                            "properties": {"cooccurrence_doc": doc_id},
                            "weight": 0.5,
                            "source_documents": [doc_id]
                        })
                        count += 1
        
        logger.info("cooccurrence_relationships_created", count=count)
        return count


import re
import json