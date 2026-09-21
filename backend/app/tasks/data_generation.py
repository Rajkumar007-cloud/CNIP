from app.tasks import celery_app

@celery_app.task(bind=True, max_retries=3)
def generate_synthetic_data(self):
    """Generate synthetic criminal network data."""
    import subprocess
    result = subprocess.run(["python", "scripts/generate_synthetic_data.py"], capture_output=True, text=True, cwd="/app")
    if result.returncode != 0:
        raise self.retry(exc=Exception(result.stderr))
    return {"status": "completed", "output": result.stdout}

@celery_app.task(bind=True, max_retries=3)
def process_documents(self):
    """Process FIR documents for entity extraction."""
    import subprocess
    result = subprocess.run(["python", "scripts/process_documents.py"], capture_output=True, text=True, cwd="/app")
    if result.returncode != 0:
        raise self.retry(exc=Exception(result.stderr))
    return {"status": "completed", "output": result.stdout}