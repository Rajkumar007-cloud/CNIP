from app.tasks import celery_app

@celery_app.task(bind=True, max_retries=3)
def extract_entities_from_text(self, text: str, source_type: str = "fir"):
    """Extract entities from text using NLP."""
    from app.services.nlp_extractor import NLPExtractor
    extractor = NLPExtractor()
    return extractor.extract_entities(text)

@celery_app.task(bind=True, max_retries=3)
def process_document_batch(self, file_paths: list):
    """Process a batch of documents."""
    results = []
    for path in file_paths:
        try:
            with open(path, 'r') as f:
                text = f.read()
            result = extract_entities_from_text.delay(text).get()
            results.append({"file": path, "entities": result})
        except Exception as e:
            results.append({"file": path, "error": str(e)})
    return results