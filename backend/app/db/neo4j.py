from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class Neo4jConnection:
    def __init__(self):
        self._driver: Driver | None = None
        self._connect()

    def _connect(self):
        try:
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_pool_size=50,
                connection_timeout=30,
            )
            self._driver.verify_connectivity()
            logger.info("neo4j_connected", uri=settings.NEO4J_URI)
        except ServiceUnavailable as e:
            logger.error("neo4j_connection_failed", error=str(e))
            raise

    @property
    def driver(self) -> Driver:
        if self._driver is None:
            self._connect()
        return self._driver

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("neo4j_disconnected")

    def query(self, cypher: str, parameters: dict | None = None, database: str | None = None):
        """Execute a read query and return records."""
        with self.driver.session(database=database) as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]

    def write_query(self, cypher: str, parameters: dict | None = None, database: str | None = None):
        """Execute a write query and return summary."""
        with self.driver.session(database=database) as session:
            result = session.run(cypher, parameters or {})
            return result.consume()

    def run_transaction(self, tx_func, *args, **kwargs):
        """Run a function in a transaction."""
        with self.driver.session() as session:
            return session.execute_write(tx_func, *args, **kwargs)


# Global instance
db = Neo4jConnection()


def get_db() -> Neo4jConnection:
    return db