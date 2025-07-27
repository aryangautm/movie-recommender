from neo4j import GraphDatabase, Driver
from .config import settings

driver: Driver = None


def get_graph_driver() -> Driver:
    """Dependency to get the Neo4j driver instance."""
    return driver


def connect_to_graph():
    """Initializes the Neo4j driver."""
    global driver
    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        driver.verify_connectivity()
        print("Successfully connected to Neo4j.")
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
        raise


def close_graph_connection():
    """Closes the Neo4j driver connection."""
    global driver
    if driver:
        driver.close()
        print("Neo4j connection closed.")
