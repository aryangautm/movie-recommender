from neo4j import GraphDatabase, Driver
from .config import settings

driver: Driver = None


def get_graph_driver() -> Driver:
    """Dependency to get the Neo4j driver instance."""
    return driver


def connect_to_graph():
    """Initializes the Neo4j driver with resilience settings."""
    global driver
    try:
        print("Initializing Neo4j driver...")
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            # --- RESILIENCE SETTINGS ---
            # Keep TCP connections alive to prevent them from being timed out
            # by network infrastructure (firewalls, load balancers, etc.).
            keep_alive=True,
            # Retire connections that have been alive for more than 1 hour.
            # This helps to proactively cycle connections and avoid issues
            # with long-lived, potentially stale connections.
            max_connection_lifetime=3600,  # seconds
        )
        # Verify connectivity on startup to catch configuration errors early.
        driver.verify_connectivity()
        print("Successfully connected to Neo4j and verified connectivity.")
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
        raise


def close_graph_connection():
    """Closes the Neo4j driver connection."""
    global driver
    if driver:
        driver.close()
        print("Neo4j connection closed.")
