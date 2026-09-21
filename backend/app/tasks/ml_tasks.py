from app.tasks import celery_app

@celery_app.task(bind=True, max_retries=3)
def compute_network_analytics(self):
    """Compute network analytics (PageRank, centrality, communities)."""
    from app.services.ml_engine import get_ml_engine
    ml_engine = get_ml_engine()
    return ml_engine.compute_all_analytics()

@celery_app.task(bind=True, max_retries=3)
def compute_risk_scores(self):
    """Compute risk scores for all entities."""
    from app.services.ml_engine import get_ml_engine
    ml_engine = get_ml_engine()
    return ml_engine.compute_risk_scores()

@celery_app.task(bind=True, max_retries=3)
def detect_anomalies(self):
    """Run anomaly detection on the network."""
    from app.services.ml_engine import get_ml_engine
    ml_engine = get_ml_engine()
    return ml_engine.detect_anomalies()