import numpy as np
import pandas as pd
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import community as community_louvain
from app.db.neo4j import get_db
from app.models.schemas import EntityType, RiskScore, CentralityScores, Community, Anomaly
import structlog
import uuid
from datetime import datetime

logger = structlog.get_logger()


class NetworkAnalyticsEngine:
    def __init__(self):
        self.db = get_db()
        self.graph: Optional[nx.Graph] = None
        self.entity_id_map: Dict[str, str] = {}  # node_id -> entity_id
        self.entity_name_map: Dict[str, str] = {}  # node_id -> entity_name
    
    def load_graph(self, min_weight: float = 0.1) -> nx.Graph:
        """Load the network graph from Neo4j."""
        cypher = """
        MATCH (n)-[r]->(m)
        WHERE r.weight >= $min_weight
        RETURN n.id as source, n.name as source_name, labels(n)[0] as source_type,
               m.id as target, m.name as target_name, labels(m)[0] as target_type,
               type(r) as rel_type, r.weight as weight, r.properties_json as props
        """
        
        results = self.db.query(cypher, {"min_weight": min_weight})
        
        G = nx.Graph()
        
        for record in results:
            source_id = record["source"]
            target_id = record["target"]
            
            # Parse properties_json if it's a string
            props = record["props"]
            if isinstance(props, str):
                import json
                try:
                    props = json.loads(props)
                except:
                    props = {}
            
            # Add nodes with attributes
            source_name = record["source_name"] or source_id
            if source_id not in G:
                G.add_node(source_id, 
                          name=source_name,
                          entity_type=record["source_type"])
                self.entity_id_map[source_id] = source_id
                self.entity_name_map[source_id] = source_name
            
            target_name = record["target_name"] or target_id
            if target_id not in G:
                G.add_node(target_id,
                          name=target_name,
                          entity_type=record["target_type"])
                self.entity_id_map[target_id] = target_id
                self.entity_name_map[target_id] = target_name
            
            # Add edge with weight
            G.add_edge(source_id, target_id, 
                      weight=record["weight"],
                      rel_type=record["rel_type"],
                      properties=props)
        
        self.graph = G
        logger.info("graph_loaded", nodes=G.number_of_nodes(), edges=G.number_of_edges())
        return G
    
    def calculate_centrality(self) -> List[CentralityScores]:
        """Calculate various centrality measures for all nodes."""
        if self.graph is None:
            self.load_graph()
        
        G = self.graph
        
        # Calculate centralities
        pagerank = nx.pagerank(G, weight="weight", max_iter=1000)
        betweenness = nx.betweenness_centrality(G, weight="weight", normalized=True)
        closeness = nx.closeness_centrality(G, distance="weight")
        eigenvector = nx.eigenvector_centrality(G, weight="weight", max_iter=1000, tol=1e-6)
        degree = dict(G.degree(weight="weight"))
        
        results = []
        for node_id in G.nodes():
            name = self.entity_name_map.get(node_id, node_id)
            results.append(CentralityScores(
                entity_id=node_id,
                entity_name=name if name else node_id,  # Ensure name is never None
                pagerank=pagerank.get(node_id, 0.0),
                betweenness=betweenness.get(node_id, 0.0),
                closeness=closeness.get(node_id, 0.0),
                eigenvector=eigenvector.get(node_id, 0.0),
                degree=int(degree.get(node_id, 0))
            ))
        
        # Sort by PageRank descending
        results.sort(key=lambda x: x.pagerank, reverse=True)
        
        logger.info("centrality_calculated", count=len(results))
        return results
    
    def detect_communities(self, resolution: float = 1.0) -> List[Community]:
        """Detect communities using Louvain method."""
        if self.graph is None:
            self.load_graph()
        
        G = self.graph
        
        # Convert to undirected for community detection
        if G.is_directed():
            G_undirected = G.to_undirected()
        else:
            G_undirected = G
        
        # Louvain community detection
        partition = community_louvain.best_partition(G_undirected, weight="weight", resolution=resolution)
        
        # Group nodes by community
        communities_dict: Dict[int, List[str]] = {}
        for node_id, comm_id in partition.items():
            if comm_id not in communities_dict:
                communities_dict[comm_id] = []
            communities_dict[comm_id].append(node_id)
        
        # Calculate modularity
        modularity = community_louvain.modularity(partition, G_undirected, weight="weight")
        
        results = []
        for comm_id, members in communities_dict.items():
            # Find key entities (highest degree in community)
            member_degrees = [(m, G_undirected.degree(m, weight="weight")) for m in members]
            member_degrees.sort(key=lambda x: x[1], reverse=True)
            key_entities = [self.entity_name_map.get(m[0], m[0]) for m in member_degrees[:3]]
            
            results.append(Community(
                community_id=comm_id,
                members=[self.entity_id_map.get(m, m) for m in members],
                size=len(members),
                modularity=modularity,
                key_entities=key_entities
            ))
        
        # Sort by size descending
        results.sort(key=lambda x: x.size, reverse=True)
        
        logger.info("communities_detected", count=len(results), modularity=modularity)
        return results
    
    def detect_anomalies(self, contamination: float = 0.05) -> List[Anomaly]:
        """Detect anomalous nodes and edges using Isolation Forest."""
        if self.graph is None:
            self.load_graph()
        
        G = self.graph
        anomalies = []
        
        # Node-level anomaly detection
        node_features = self._extract_node_features(G)
        if len(node_features) > 10:  # Need minimum samples
            node_ids = list(node_features.keys())
            X = np.array([node_features[nid] for nid in node_ids])
            
            # Normalize features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Isolation Forest
            iso_forest = IsolationForest(contamination=contamination, random_state=42, n_estimators=200)
            predictions = iso_forest.fit_predict(X_scaled)
            scores = iso_forest.decision_function(X_scaled)
            
            for i, (node_id, pred) in enumerate(zip(node_ids, predictions)):
                if pred == -1:  # Anomaly
                    anomaly_score = -scores[i]  # Higher = more anomalous
                    
                    anomalies.append(Anomaly(
                        entity_id=node_id,
                        entity_name=self.entity_name_map.get(node_id, node_id),
                        anomaly_type="structural_anomaly",
                        score=float(anomaly_score),
                        description=f"Node exhibits unusual network structure (degree: {G.degree(node_id, weight='weight'):.1f}, "
                                  f"clustering: {nx.clustering(G, node_id, weight='weight'):.3f})",
                        evidence=[f"Isolation Forest score: {anomaly_score:.3f}"],
                        timestamp=datetime.now()
                    ))
        
        # Edge-level anomaly detection (unusual transaction amounts, call patterns)
        edge_anomalies = self._detect_edge_anomalies(G)
        anomalies.extend(edge_anomalies)
        
        # Temporal anomalies (burst patterns)
        temporal_anomalies = self._detect_temporal_anomalies()
        anomalies.extend(temporal_anomalies)
        
        logger.info("anomalies_detected", count=len(anomalies))
        return anomalies
    
    def _extract_node_features(self, G: nx.Graph) -> Dict[str, List[float]]:
        """Extract numerical features for each node."""
        features = {}
        
        # Pre-compute some global metrics
        avg_degree = np.mean([d for _, d in G.degree(weight="weight")])
        avg_clustering = nx.average_clustering(G, weight="weight")
        
        for node in G.nodes():
            deg = G.degree(node, weight="weight")
            clust = nx.clustering(G, node, weight="weight")
            
            # Ego network features
            ego = nx.ego_graph(G, node, radius=2)
            ego_size = ego.number_of_nodes()
            ego_edges = ego.number_of_edges()
            ego_density = nx.density(ego) if ego_size > 1 else 0
            
            # Neighbor degree statistics
            neighbor_degrees = [G.degree(n, weight="weight") for n in G.neighbors(node)]
            avg_neighbor_deg = np.mean(neighbor_degrees) if neighbor_degrees else 0
            max_neighbor_deg = np.max(neighbor_degrees) if neighbor_degrees else 0
            
            features[node] = [
                deg,
                clust,
                ego_size,
                ego_edges,
                ego_density,
                avg_neighbor_deg,
                max_neighbor_deg,
                deg / max(avg_degree, 1),
                clust / max(avg_clustering, 0.001)
            ]
        
        return features
    
    def _detect_edge_anomalies(self, G: nx.Graph) -> List[Anomaly]:
        """Detect anomalous edges (transactions, calls)."""
        anomalies = []
        
        # Get edge weights
        weights = [G[u][v].get("weight", 1.0) for u, v in G.edges()]
        if len(weights) < 10:
            return anomalies
        
        weights_array = np.array(weights).reshape(-1, 1)
        
        # Isolation Forest on edge weights
        iso_forest = IsolationForest(contamination=0.02, random_state=42)
        predictions = iso_forest.fit_predict(weights_array)
        scores = iso_forest.decision_function(weights_array)
        
        for i, (u, v) in enumerate(G.edges()):
            if predictions[i] == -1:
                weight = G[u][v].get("weight", 1.0)
                rel_type = G[u][v].get("rel_type", "UNKNOWN")
                
                anomalies.append(Anomaly(
                    entity_id=f"{u}->{v}",
                    entity_name=f"{self.entity_name_map.get(u, u)} -> {self.entity_name_map.get(v, v)}",
                    anomaly_type="edge_weight_anomaly",
                    score=float(-scores[i]),
                    description=f"Unusual {rel_type} weight: {weight:.2f} (mean: {np.mean(weights):.2f}, std: {np.std(weights):.2f})",
                    evidence=[f"Edge weight: {weight:.2f}", f"Z-score: {(weight - np.mean(weights)) / np.std(weights):.2f}"],
                    timestamp=datetime.now()
                ))
        
        return anomalies
    
    def _detect_temporal_anomalies(self) -> List[Anomaly]:
        """Detect temporal anomalies (burst patterns)."""
        anomalies = []
        
        # Query for temporal patterns in CDR data
        cypher = """
        MATCH ()-[r:CONTACTED]->()
        WHERE r.properties_json IS NOT NULL
        RETURN r.properties_json as props, count(*) as call_count
        """
        
        try:
            results = self.db.query(cypher)
            if len(results) > 20:
                df = pd.DataFrame(results)
                # Parse timestamp from props JSON
                def extract_timestamp(props):
                    if isinstance(props, str):
                        import json
                        try:
                            return json.loads(props).get("timestamp")
                        except:
                            return None
                    elif isinstance(props, dict):
                        return props.get("timestamp")
                    return None
                
                df["timestamp"] = df["props"].apply(extract_timestamp)
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
                df = df.dropna()
                
                if len(df) > 20:
                    # Resample to hourly buckets
                    df.set_index("timestamp", inplace=True)
                    hourly = df["call_count"].resample("1H").sum()
                    
                    # Detect bursts using rolling statistics
                    rolling_mean = hourly.rolling(window=24, center=True).mean()
                    rolling_std = hourly.rolling(window=24, center=True).std()
                    
                    # Z-score based burst detection
                    z_scores = (hourly - rolling_mean) / (rolling_std + 1e-6)
                    bursts = hourly[z_scores > 3]
                    
                    for ts, count in bursts.items():
                        anomalies.append(Anomaly(
                            entity_id=f"temporal_burst_{ts.isoformat()}",
                            entity_name=f"Call burst at {ts}",
                            anomaly_type="temporal_burst",
                            score=float(z_scores.loc[ts]),
                            description=f"Unusual call volume spike: {count} calls in 1 hour (expected ~{rolling_mean.loc[ts]:.1f})",
                            evidence=[f"Call count: {count}", f"Z-score: {z_scores.loc[ts]:.2f}"],
                            timestamp=ts.to_pydatetime()
                        ))
        except Exception as e:
            logger.warning("temporal_anomaly_detection_failed", error=str(e))
        
        return anomalies
    
    def calculate_risk_scores(self, 
                              centrality_weight: float = 0.4,
                              anomaly_weight: float = 0.4,
                              betweenness_weight: float = 0.2) -> List[RiskScore]:
        """Calculate composite risk scores for all entities."""
        if self.graph is None:
            self.load_graph()
        
        # Get centrality scores
        centrality_results = self.calculate_centrality()
        
        # Get anomalies
        anomalies = self.detect_anomalies()
        anomaly_dict = {a.entity_id: a.score for a in anomalies}
        
        # Normalize centrality scores
        max_pagerank = max((c.pagerank for c in centrality_results), default=1)
        max_betweenness = max((c.betweenness for c in centrality_results), default=1)
        
        risk_scores = []
        
        for i, cent in enumerate(centrality_results):
            entity_id = cent.entity_id
            
            # Normalize
            norm_pagerank = cent.pagerank / max_pagerank if max_pagerank > 0 else 0
            norm_betweenness = cent.betweenness / max_betweenness if max_betweenness > 0 else 0
            anomaly_score = anomaly_dict.get(entity_id, 0)
            
            # Composite risk score
            risk = (
                centrality_weight * norm_pagerank +
                betweenness_weight * norm_betweenness +
                anomaly_weight * min(anomaly_score, 1.0)
            ) * 100
            
            risk_scores.append(RiskScore(
                entity_id=entity_id,
                entity_name=cent.entity_name,
                entity_type=EntityType.OTHER,  # Will be enriched from graph
                risk_score=min(100, max(0, risk)),
                network_influence=norm_pagerank,
                anomaly_score=anomaly_score,
                factors={
                    "pagerank": norm_pagerank,
                    "betweenness": norm_betweenness,
                    "anomaly": min(anomaly_score, 1.0)
                },
                rank=0  # Will be set after sorting
            ))
        
        # Sort by risk score and assign ranks
        risk_scores.sort(key=lambda x: x.risk_score, reverse=True)
        for rank, rs in enumerate(risk_scores, 1):
            rs.rank = rank
        
        logger.info("risk_scores_calculated", count=len(risk_scores))
        return risk_scores
    
    def find_shortest_path(self, source_id: str, target_id: str, max_depth: int = 6) -> Optional[List[Dict]]:
        """Find shortest path between two entities."""
        if self.graph is None:
            self.load_graph()
        
        G = self.graph
        
        try:
            if source_id not in G or target_id not in G:
                return None
            
            path = nx.shortest_path(G, source_id, target_id, weight="weight")
            
            if len(path) - 1 > max_depth:
                return None
            
            result = []
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                edge_data = G[u][v]
                result.append({
                    "source": self.entity_name_map.get(u, u),
                    "target": self.entity_name_map.get(v, v),
                    "relationship": edge_data.get("rel_type", "CONNECTED"),
                    "weight": edge_data.get("weight", 1.0)
                })
            
            return result
            
        except nx.NetworkXNoPath:
            return None
    
    def get_ego_network(self, entity_id: str, radius: int = 2) -> Dict[str, Any]:
        """Get ego network for an entity."""
        if self.graph is None:
            self.load_graph()
        
        G = self.graph
        
        if entity_id not in G:
            return {"nodes": [], "links": []}
        
        ego = nx.ego_graph(G, entity_id, radius=radius)
        
        nodes = []
        for nid in ego.nodes():
            nodes.append({
                "id": nid,
                "label": self.entity_name_map.get(nid, nid),
                "entity_type": G.nodes[nid].get("entity_type", "Unknown"),
                "is_ego": nid == entity_id
            })
        
        links = []
        for u, v, data in ego.edges(data=True):
            links.append({
                "source": u,
                "target": v,
                "relationship": data.get("rel_type", "CONNECTED"),
                "weight": data.get("weight", 1.0)
            })
        
        return {"nodes": nodes, "links": links}


class MLEngine:
    """High-level ML engine combining all analytics."""
    
    def __init__(self):
        self.analytics = NetworkAnalyticsEngine()
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete network analysis."""
        logger.info("starting_full_analysis")
        
        # Load graph
        self.analytics.load_graph()
        
        # Calculate all metrics
        centrality = self.analytics.calculate_centrality()
        communities = self.analytics.detect_communities()
        anomalies = self.analytics.detect_anomalies()
        risk_scores = self.analytics.calculate_risk_scores()
        
        # Network statistics
        G = self.analytics.graph
        stats = {
            "total_entities": G.number_of_nodes(),
            "total_relationships": G.number_of_edges(),
            "density": nx.density(G),
            "avg_clustering": nx.average_clustering(G, weight="weight"),
            "connected_components": nx.number_connected_components(G),
            "communities_found": len(communities),
            "anomalies_found": len(anomalies),
            "high_risk_entities": len([r for r in risk_scores if r.risk_score > 70])
        }
        
        logger.info("full_analysis_complete", **stats)
        
        return {
            "centrality": [c.model_dump() for c in centrality],
            "communities": [c.model_dump() for c in communities],
            "anomalies": [a.model_dump() for a in anomalies],
            "risk_scores": [r.model_dump() for r in risk_scores],
            "statistics": stats
        }
    
    def get_entity_profile(self, entity_id: str) -> Dict[str, Any]:
        """Get comprehensive profile for a single entity."""
        if self.analytics.graph is None:
            self.analytics.load_graph()
        
        G = self.analytics.graph
        
        if entity_id not in G:
            return {"error": "Entity not found"}
        
        # Centrality for this entity
        centrality = self.analytics.calculate_centrality()
        entity_centrality = next((c for c in centrality if c.entity_id == entity_id), None)
        
        # Ego network
        ego = self.analytics.get_ego_network(entity_id, radius=2)
        
        # Risk score
        risk_scores = self.analytics.calculate_risk_scores()
        entity_risk = next((r for r in risk_scores if r.entity_id == entity_id), None)
        
        # Anomalies involving this entity
        anomalies = self.analytics.detect_anomalies()
        entity_anomalies = [a for a in anomalies if entity_id in a.entity_id]
        
        # Direct neighbors
        neighbors = []
        for nbr in G.neighbors(entity_id):
            edge_data = G[entity_id][nbr]
            neighbors.append({
                "entity_id": nbr,
                "name": self.analytics.entity_name_map.get(nbr, nbr),
                "entity_type": G.nodes[nbr].get("entity_type", "Unknown"),
                "relationship": edge_data.get("rel_type", "CONNECTED"),
                "weight": edge_data.get("weight", 1.0)
            })
        
        return {
            "entity_id": entity_id,
            "name": self.analytics.entity_name_map.get(entity_id, entity_id),
            "entity_type": G.nodes[entity_id].get("entity_type", "Unknown"),
            "centrality": entity_centrality.model_dump() if entity_centrality else None,
            "risk_score": entity_risk.model_dump() if entity_risk else None,
            "anomalies": [a.model_dump() for a in entity_anomalies],
            "neighbors": neighbors,
            "ego_network": ego,
            "degree": G.degree(entity_id, weight="weight"),
            "clustering": nx.clustering(G, entity_id, weight="weight")
        }


# Global instance
ml_engine = MLEngine()


def get_ml_engine() -> MLEngine:
    return ml_engine