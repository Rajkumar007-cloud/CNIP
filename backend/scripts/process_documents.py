#!/usr/bin/env python3
"""
Document Processing Script for Criminal Network Intelligence Platform
Processes FIR reports, surveillance documents, and other text files
to extract entities and build the knowledge graph.
"""

import os
import json
import glob
from pathlib import Path
from typing import List, Dict, Any
import structlog

from app.services.nlp_extractor import get_extractor
from app.services.graph_builder import GraphBuilder

logger = structlog.get_logger()


class DocumentProcessor:
    def __init__(self):
        self.extractor = get_extractor()
        self.builder = GraphBuilder()
    
    def process_fir_reports(self, directory: str = "data/fir_reports") -> Dict[str, Any]:
        """Process all FIR reports in a directory."""
        logger.info("processing_fir_reports", directory=directory)
        
        fir_files = glob.glob(os.path.join(directory, "*.txt")) + \
                    glob.glob(os.path.join(directory, "*.pdf")) + \
                    glob.glob(os.path.join(directory, "*.docx"))
        
        if not fir_files:
            logger.warning("no_fir_files_found", directory=directory)
            return {"processed": 0, "entities": 0, "relationships": 0}
        
        all_entities = []
        processed_count = 0
        
        for file_path in fir_files:
            try:
                entities = self._process_single_file(file_path, "fir")
                all_entities.extend(entities)
                processed_count += 1
                logger.info("fir_processed", file=os.path.basename(file_path), entities=len(entities))
            except Exception as e:
                logger.error("fir_processing_failed", file=file_path, error=str(e))
        
        # Build graph from all entities
        if all_entities:
            entity_map = self.builder.build_from_entities(all_entities)
            
            # Add graph IDs to entities
            for ent in all_entities:
                ent["graph_id"] = entity_map.get(ent["text"].lower().strip())
            
            # Create co-occurrence relationships
            self.builder.link_entities_cooccurrence(all_entities)
            
            logger.info("fir_graph_built", entities=len(entity_map), relationships="co-occurrence")
        
        return {
            "processed": processed_count,
            "entities": len(all_entities),
            "unique_entities": len(entity_map) if all_entities else 0
        }
    
    def process_surveillance_reports(self, directory: str = "data/surveillance") -> Dict[str, Any]:
        """Process surveillance reports."""
        logger.info("processing_surveillance_reports", directory=directory)
        
        files = glob.glob(os.path.join(directory, "*.txt")) + \
                glob.glob(os.path.join(directory, "*.json"))
        
        all_entities = []
        processed_count = 0
        
        for file_path in files:
            try:
                entities = self._process_single_file(file_path, "surveillance")
                all_entities.extend(entities)
                processed_count += 1
            except Exception as e:
                logger.error("surveillance_processing_failed", file=file_path, error=str(e))
        
        if all_entities:
            entity_map = self.builder.build_from_entities(all_entities)
            for ent in all_entities:
                ent["graph_id"] = entity_map.get(ent["text"].lower().strip())
            self.builder.link_entities_cooccurrence(all_entities)
        
        return {
            "processed": processed_count,
            "entities": len(all_entities),
            "unique_entities": len(entity_map) if all_entities else 0
        }
    
    def process_cdr_files(self, directory: str = "data/cdr") -> Dict[str, Any]:
        """Process CDR files (CSV/Excel)."""
        logger.info("processing_cdr_files", directory=directory)
        
        import pandas as pd
        
        files = glob.glob(os.path.join(directory, "*.csv")) + \
                glob.glob(os.path.join(directory, "*.xlsx")) + \
                glob.glob(os.path.join(directory, "*.xls"))
        
        total_records = 0
        processed_count = 0
        
        for file_path in files:
            try:
                df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
                
                # Standardize column names
                df.columns = df.columns.str.lower().str.strip()
                
                caller_col = self._find_column(df, ['caller', 'calling_number', 'source', 'from', 'origin'])
                receiver_col = self._find_column(df, ['receiver', 'called_number', 'target', 'to', 'destination'])
                
                if not caller_col or not receiver_col:
                    logger.warning("cdr_columns_not_found", file=file_path, columns=list(df.columns))
                    continue
                
                records = df[[caller_col, receiver_col]].rename(
                    columns={caller_col: 'caller', receiver_col: 'receiver'}
                ).to_dict('records')
                
                # Add metadata
                for record in records:
                    record['source_file'] = os.path.basename(file_path)
                
                self.builder.build_cdr_relationships(records)
                total_records += len(records)
                processed_count += 1
                
                logger.info("cdr_processed", file=os.path.basename(file_path), records=len(records))
                
            except Exception as e:
                logger.error("cdr_processing_failed", file=file_path, error=str(e))
        
        return {
            "processed": processed_count,
            "total_records": total_records
        }
    
    def process_financial_files(self, directory: str = "data/financial") -> Dict[str, Any]:
        """Process financial transaction files."""
        logger.info("processing_financial_files", directory=directory)
        
        import pandas as pd
        
        files = glob.glob(os.path.join(directory, "*.csv")) + \
                glob.glob(os.path.join(directory, "*.xlsx"))
        
        total_transactions = 0
        processed_count = 0
        
        for file_path in files:
            try:
                df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
                
                df.columns = df.columns.str.lower().str.strip()
                
                sender_col = self._find_column(df, ['sender', 'from_account', 'origin', 'debit_account'])
                receiver_col = self._find_column(df, ['receiver', 'to_account', 'destination', 'credit_account'])
                amount_col = self._find_column(df, ['amount', 'value', 'txn_amount', 'transaction_amount'])
                
                if not sender_col or not receiver_col:
                    logger.warning("financial_columns_not_found", file=file_path, columns=list(df.columns))
                    continue
                
                transactions = []
                for _, row in df.iterrows():
                    txn = {
                        'sender': str(row[sender_col]),
                        'receiver': str(row[receiver_col]),
                        'amount': float(row[amount_col]) if amount_col and amount_col in row else 0,
                        'source_file': os.path.basename(file_path)
                    }
                    # Add other columns as properties
                    for col in df.columns:
                        if col not in [sender_col, receiver_col, amount_col]:
                            txn[col] = row[col]
                    transactions.append(txn)
                
                self.builder.build_financial_relationships(transactions)
                total_transactions += len(transactions)
                processed_count += 1
                
                logger.info("financial_processed", file=os.path.basename(file_path), transactions=len(transactions))
                
            except Exception as e:
                logger.error("financial_processing_failed", file=file_path, error=str(e))
        
        return {
            "processed": processed_count,
            "total_transactions": total_transactions
        }
    
    def _process_single_file(self, file_path: str, doc_type: str) -> List[Dict[str, Any]]:
        """Process a single text file."""
        content = self._read_file(file_path)
        if not content:
            return []
        
        doc_id = os.path.basename(file_path)
        entities = self.extractor.extract_entities(content, doc_id)
        
        # Add document metadata
        for ent in entities:
            ent["document_id"] = doc_id
            ent["document_type"] = doc_type
        
        return entities
    
    def _read_file(self, file_path: str) -> str:
        """Read file content based on extension."""
        ext = Path(file_path).suffix.lower()
        
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext == '.pdf':
            try:
                import pdfplumber
                text = []
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text.append(page.extract_text() or '')
                return '\n'.join(text)
            except ImportError:
                logger.warning("pdfplumber_not_installed", file=file_path)
                return ""
        elif ext == '.docx':
            try:
                from docx import Document
                doc = Document(file_path)
                return '\n'.join([p.text for p in doc.paragraphs])
            except ImportError:
                logger.warning("python-docx_not_installed", file=file_path)
                return ""
        elif ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # If it's a list of reports, concatenate content
                if isinstance(data, list):
                    return '\n'.join([item.get('content', '') for item in data if isinstance(item, dict)])
                return data.get('content', '')
        else:
            logger.warning("unsupported_file_type", file=file_path, ext=ext)
            return ""
    
    def _find_column(self, df, possible_names: List[str]) -> str | None:
        """Find column by checking possible names."""
        cols_lower = {c.lower(): c for c in df.columns}
        for name in possible_names:
            if name.lower() in cols_lower:
                return cols_lower[name.lower()]
        return None


def main():
    """Main entry point."""
    import sys
    
    processor = DocumentProcessor()
    
    # Process all data directories
    results = {}
    
    # FIR Reports
    if os.path.exists("data/fir_reports"):
        results['fir'] = processor.process_fir_reports("data/fir_reports")
    
    # Surveillance Reports
    if os.path.exists("data/surveillance"):
        results['surveillance'] = processor.process_surveillance_reports("data/surveillance")
    
    # CDR Files
    if os.path.exists("data/cdr"):
        results['cdr'] = processor.process_cdr_files("data/cdr")
    
    # Financial Files
    if os.path.exists("data/financial"):
        results['financial'] = processor.process_financial_files("data/financial")
    
    print("\n=== Document Processing Complete ===")
    for doc_type, result in results.items():
        print(f"  {doc_type}: {result}")
    print("====================================\n")


if __name__ == "__main__":
    main()