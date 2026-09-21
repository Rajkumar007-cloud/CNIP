import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span
from typing import List, Dict, Any, Optional
import re
from app.core.config import settings
import structlog

logger = structlog.get_logger()


@Language.component("custom_entity_ruler")
def custom_entity_ruler(doc: Doc) -> Doc:
    """Custom entity ruler for domain-specific patterns."""
    patterns = [
        # Indian phone numbers
        {"label": "PHONE_NUMBER", "pattern": [{"TEXT": {"REGEX": r"^\+?91[\s-]?\d{10}$"}}]},
        {"label": "PHONE_NUMBER", "pattern": [{"TEXT": {"REGEX": r"^\d{10}$"}}]},
        {"label": "PHONE_NUMBER", "pattern": [{"TEXT": {"REGEX": r"^\+?\d{3}[\s-]?\d{3}[\s-]?\d{4}$"}}]},
        
        # Bank account patterns
        {"label": "BANK_ACCOUNT", "pattern": [{"TEXT": {"REGEX": r"^[A-Z]{4}0[A-Z0-9]{16}$"}}]},  # IFSC
        {"label": "BANK_ACCOUNT", "pattern": [{"TEXT": {"REGEX": r"^\d{9,18}$"}}]},
        
        # Vehicle registration (Indian format)
        {"label": "VEHICLE", "pattern": [{"TEXT": {"REGEX": r"^[A-Z]{2}[\s-]?\d{2}[\s-]?[A-Z]{1,2}[\s-]?\d{4}$"}}]},
        
        # PAN Card
        {"label": "ID_NUMBER", "pattern": [{"TEXT": {"REGEX": r"^[A-Z]{5}\d{4}[A-Z]$"}}]},
        
        # Aadhaar (masked)
        {"label": "ID_NUMBER", "pattern": [{"TEXT": {"REGEX": r"^\d{4}[\s-]?\d{4}[\s-]?\d{4}$"}}]},
        
        # Crypto wallet addresses (basic patterns)
        {"label": "CRYPTO_WALLET", "pattern": [{"TEXT": {"REGEX": r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$"}}]},  # Bitcoin
        {"label": "CRYPTO_WALLET", "pattern": [{"TEXT": {"REGEX": r"^0x[a-fA-F0-9]{40}$"}}]},  # Ethereum
        
        # Email
        {"label": "EMAIL", "pattern": [{"TEXT": {"REGEX": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"}}]},
        
        # Social handles
        {"label": "SOCIAL_HANDLE", "pattern": [{"TEXT": {"REGEX": r"^@[a-zA-Z0-9_]{1,15}$"}}]},
        {"label": "SOCIAL_HANDLE", "pattern": [{"TEXT": {"REGEX": r"^#[a-zA-Z0-9_]{1,30}$"}}]},
    ]
    
    ruler = doc.vocab.nlp.get_pipe("entity_ruler") if "entity_ruler" in doc.vocab.nlp.pipe_names else None
    if ruler:
        ruler.add_patterns(patterns)
    
    return doc


class EntityExtractor:
    def __init__(self):
        self.nlp = None
        self._load_model()
    
    def _load_model(self):
        try:
            self.nlp = spacy.load(settings.SPACY_MODEL)
            logger.info("spacy_model_loaded", model=settings.SPACY_MODEL)
            
            # Add custom entity ruler if not present
            if "entity_ruler" not in self.nlp.pipe_names:
                ruler = self.nlp.add_pipe("entity_ruler", before="ner")
                logger.info("entity_ruler_added")
            
            # Add custom patterns
            self._add_custom_patterns()
            
        except OSError:
            logger.warning("spacy_model_not_found", model=settings.SPACY_MODEL)
            logger.info("downloading_spacy_model")
            spacy.cli.download(settings.SPACY_MODEL)
            self.nlp = spacy.load(settings.SPACY_MODEL)
            self._add_custom_patterns()
    
    def _add_custom_patterns(self):
        patterns = [
            # Indian phone numbers
            {"label": "PHONE_NUMBER", "pattern": [{"TEXT": {"REGEX": r"^\+?91[\s-]?\d{10}$"}}]},
            {"label": "PHONE_NUMBER", "pattern": [{"TEXT": {"REGEX": r"^\d{10}$"}}]},
            {"label": "PHONE_NUMBER", "pattern": [{"TEXT": {"REGEX": r"^\+?\d{3}[\s-]?\d{3}[\s-]?\d{4}$"}}]},
            
            # Bank account patterns
            {"label": "BANK_ACCOUNT", "pattern": [{"TEXT": {"REGEX": r"^[A-Z]{4}0[A-Z0-9]{16}$"}}]},
            {"label": "BANK_ACCOUNT", "pattern": [{"TEXT": {"REGEX": r"^\d{9,18}$"}}]},
            
            # Vehicle registration (Indian format)
            {"label": "VEHICLE", "pattern": [{"TEXT": {"REGEX": r"^[A-Z]{2}[\s-]?\d{2}[\s-]?[A-Z]{1,2}[\s-]?\d{4}$"}}]},
            
            # PAN Card
            {"label": "ID_NUMBER", "pattern": [{"TEXT": {"REGEX": r"^[A-Z]{5}\d{4}[A-Z]$"}}]},
            
            # Aadhaar (masked)
            {"label": "ID_NUMBER", "pattern": [{"TEXT": {"REGEX": r"^\d{4}[\s-]?\d{4}[\s-]?\d{4}$"}}]},
            
            # Crypto wallet addresses
            {"label": "CRYPTO_WALLET", "pattern": [{"TEXT": {"REGEX": r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$"}}]},
            {"label": "CRYPTO_WALLET", "pattern": [{"TEXT": {"REGEX": r"^0x[a-fA-F0-9]{40}$"}}]},
            
            # Email
            {"label": "EMAIL", "pattern": [{"TEXT": {"REGEX": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"}}]},
            
            # Social handles
            {"label": "SOCIAL_HANDLE", "pattern": [{"TEXT": {"REGEX": r"^@[a-zA-Z0-9_]{1,15}$"}}]},
            {"label": "SOCIAL_HANDLE", "pattern": [{"TEXT": {"REGEX": r"^#[a-zA-Z0-9_]{1,30}$"}}]},
        ]
        
        ruler = self.nlp.get_pipe("entity_ruler")
        ruler.add_patterns(patterns)
        logger.info("custom_patterns_added", count=len(patterns))
    
    def extract_entities(self, text: str, source_document: str = "") -> List[Dict[str, Any]]:
        """Extract entities from text using spaCy NER + custom rules."""
        doc = self.nlp(text)
        
        entities = []
        seen = set()
        
        for ent in doc.ents:
            # Filter for relevant entity types
            if ent.label_ in [
                "PERSON", "ORG", "GPE", "LOC", "FAC", 
                "PHONE_NUMBER", "BANK_ACCOUNT", "VEHICLE",
                "ID_NUMBER", "CRYPTO_WALLET", "EMAIL", "SOCIAL_HANDLE",
                "DATE", "TIME", "MONEY", "EVENT", "LAW", "PRODUCT"
            ]:
                # Create unique key to deduplicate
                key = (ent.text.lower().strip(), ent.label_)
                if key not in seen:
                    seen.add(key)
                    
                    # Map spaCy labels to our entity types
                    entity_type = self._map_label(ent.label_)
                    
                    entities.append({
                        "text": ent.text.strip(),
                        "label": ent.label_,
                        "entity_type": entity_type,
                        "start_char": ent.start_char,
                        "end_char": ent.end_char,
                        "source_document": source_document,
                        "confidence": 0.9 if ent.label_ in ["PERSON", "ORG", "GPE"] else 0.8
                    })
        
        return entities
    
    def _map_label(self, spacy_label: str) -> str:
        """Map spaCy entity labels to our entity types."""
        mapping = {
            "PERSON": "Person",
            "ORG": "Organization",
            "GPE": "Location",
            "LOC": "Location",
            "FAC": "Location",
            "PHONE_NUMBER": "PhoneNumber",
            "BANK_ACCOUNT": "BankAccount",
            "VEHICLE": "Vehicle",
            "ID_NUMBER": "IdNumber",
            "CRYPTO_WALLET": "CryptoWallet",
            "EMAIL": "Email",
            "SOCIAL_HANDLE": "SocialHandle",
            "DATE": "Date",
            "TIME": "Time",
            "MONEY": "Money",
            "EVENT": "Event",
            "LAW": "Law",
            "PRODUCT": "Product",
        }
        return mapping.get(spacy_label, "Other")
    
    def extract_from_documents(self, documents: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Extract entities from multiple documents."""
        all_entities = []
        
        for doc in documents:
            text = doc.get("content", "")
            source = doc.get("source", "unknown")
            doc_id = doc.get("id", source)
            
            entities = self.extract_entities(text, doc_id)
            for ent in entities:
                ent["source_document"] = source
                ent["document_id"] = doc_id
            
            all_entities.extend(entities)
        
        # Deduplicate across documents
        seen = set()
        unique_entities = []
        for ent in all_entities:
            key = (ent["text"].lower().strip(), ent["entity_type"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(ent)
        
        return unique_entities


# Global extractor instance
extractor = EntityExtractor()


def get_extractor() -> EntityExtractor:
    return extractor