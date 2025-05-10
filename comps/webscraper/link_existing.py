import os
import requests
import logging
import re
from typing import Optional, List, Dict, Any
from neo4j import GraphDatabase
from datetime import datetime
from pathlib import Path # Import Path

# --- Configuration ---
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
API_SERVER_HOST = os.getenv("SERVER_HOST_IP", "localhost")
API_SERVER_PORT = os.getenv("SERVER_PORT", "9001")
API_ENDPOINT = f"http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/circulars"

# --- Define PDF Directory ---
# Assumes this script is run from the root 'easy-circulars' directory
# Or adjust relative path if run from 'comps/webscraper'
PDF_DIR = Path("ui/public/pdfs")
# If running from comps/webscraper: PDF_DIR = Path(__file__).parent.parent.parent / "ui" / "public" / "pdfs"


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("link_existing")

# --- Neo4j Connection ---
_neo4j_driver = None

def connect_neo4j():
    """Establishes connection to the Neo4j database."""
    global _neo4j_driver
    try:
        _neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        _neo4j_driver.verify_connectivity()
        logger.info(f"Successfully connected to Neo4j at {NEO4J_URI}")
        return _neo4j_driver
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        _neo4j_driver = None
        return None

def close_neo4j_driver():
    """Closes the Neo4j driver connection."""
    global _neo4j_driver
    if _neo4j_driver is not None:
        logger.info("Closing Neo4j driver connection.")
        _neo4j_driver.close()
        _neo4j_driver = None

# --- Helper Functions ---
def parse_core_id(full_id: str) -> Optional[str]:
    """
    Parses the core identifier from the full circular ID string.
    Attempts to extract patterns like 'XX.XX.XXX'.
    """
    if not full_id:
        return None
    core_id_match = re.search(r'(\d{2}\.\d{2}\.\d+)', full_id)
    if core_id_match:
        return core_id_match.group(1)
    return None

# --- Modified Metadata Fetch ---
def fetch_metadata_map() -> Dict[str, Dict[str, Any]]:
    """Fetches circular metadata from the API and returns a map keyed by relative path."""
    logger.info(f"Fetching circular metadata from {API_ENDPOINT}...")
    metadata_map = {}
    try:
        response = requests.get(API_ENDPOINT, timeout=60) # Increased timeout
        response.raise_for_status()
        metadata_list = response.json()
        if isinstance(metadata_list, list):
            for item in metadata_list:
                path = item.get('path')
                # Ensure path starts with /pdfs/ for consistency
                if path and not path.startswith('/'):
                    path = '/' + path
                if path and path.startswith('/pdfs/'):
                    metadata_map[path] = item
                else:
                    logger.warning(f"Skipping record with invalid or missing path: {item.get('circular_id')}")
            logger.info(f"Successfully fetched and mapped {len(metadata_map)} circular records by path.")
            return metadata_map
        else:
            logger.error(f"API response is not a list: {type(metadata_list)}")
            return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching metadata from API: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error processing API response: {e}")
        return {}

# --- Function to Scan Local PDFs ---
def get_local_pdf_paths(pdf_directory: Path) -> List[str]:
    """Scans the directory and returns a list of relative PDF paths (e.g., /pdfs/file.pdf)."""
    local_paths = []
    if not pdf_directory.is_dir():
        logger.error(f"PDF directory not found: {pdf_directory}")
        return []
    for item in pdf_directory.iterdir():
        if item.is_file() and item.suffix.lower() == '.pdf':
            # Construct relative path like /pdfs/filename.pdf
            relative_path = f"/pdfs/{item.name}"
            local_paths.append(relative_path)
    logger.info(f"Found {len(local_paths)} PDF files locally in {pdf_directory}.")
    return local_paths


# --- Neo4j Node Creation/Update Function ---
def create_update_circular_node(driver: GraphDatabase.driver, circular_data: Dict[str, Any]):
    """
    Creates or updates a circular node in Neo4j based on its unique identifier.
    Does NOT create relationships.
    Uses 'pdf_url' or 'path' as the primary identifier.
    """
    unique_id_prop = 'pdf_url'
    unique_id_value = circular_data.get('pdf_url')
    if not unique_id_value:
         unique_id_prop = 'path'
         unique_id_value = circular_data.get('path')

    if not unique_id_value:
        logger.warning(f"Skipping node creation due to missing 'pdf_url' or 'path': {circular_data.get('circular_id')}")
        return

    full_id = circular_data.get('circular_id')
    core_id = parse_core_id(full_id)
    title = circular_data.get('title')

    # --- Date Parsing ---
    date_val = circular_data.get('date')
    neo4j_date_str = None
    if date_val:
        try:
            dt_obj = None
            if isinstance(date_val, str):
                 if date_val.endswith('Z'):
                     date_val = date_val[:-1] + '+00:00'
                 if 'T' not in date_val:
                      try:
                          dt_obj = datetime.strptime(date_val, '%Y-%m-%d')
                      except ValueError:
                          date_val += 'T00:00:00+00:00'
                          dt_obj = datetime.fromisoformat(date_val)
                 else:
                     dt_obj = datetime.fromisoformat(date_val)
            elif isinstance(date_val, datetime):
                 dt_obj = date_val
            if dt_obj:
                neo4j_date_str = dt_obj.isoformat()
        except ValueError as ve:
             logger.warning(f"Could not parse date '{date_val}' for {unique_id_value}: {ve}")
        except Exception as e:
             logger.error(f"Unexpected error parsing date '{date_val}' for {unique_id_value}: {e}")


    # --- Cypher Query to ONLY Merge Node ---
    query = f"""
    MERGE (c:Circular {{{unique_id_prop}: $unique_id_value}})
    ON CREATE SET
        c._id = $_id,
        c.title = $title,
        c.core_id = $core_id,
        c.date = CASE WHEN $_date_str IS NOT NULL THEN datetime($_date_str) ELSE null END,
        c.url = $url,
        c.path = $path,
        c.pdf_url = $pdf_url,
        c.created_at = timestamp()
    ON MATCH SET
        c._id = $_id,
        c.title = $title,
        c.core_id = $core_id,
        c.date = CASE WHEN $_date_str IS NOT NULL THEN datetime($_date_str) ELSE c.date END,
        c.url = $url,
        c.path = $path,
        c.pdf_url = $pdf_url,
        c.updated_at = timestamp()
    """
    # --- Parameters ---
    params = {
        "unique_id_value": unique_id_value,
        "_id": full_id,
        "title": title,
        "core_id": core_id,
        "_date_str": neo4j_date_str,
        "url": circular_data.get('url'),
        "path": circular_data.get('path'),
        "pdf_url": circular_data.get('pdf_url')
    }

    try:
        with driver.session() as session:
            session.run(query, params)
            
    except Exception as e:
        logger.error(f"Failed to execute Neo4j node merge for {unique_id_value}: {e}")
        logger.error(f"Query Params: {params}")


def link_circular_versions(driver: GraphDatabase.driver):
    """
    Creates NEXT_VERSION relationships between circulars based on
    matching core_id, title, and sequential date.
    """
    logger.info("Attempting to link circular versions (NEXT_VERSION)...")

    
    delete_query = "MATCH (:Circular)-[r:NEXT_VERSION]->(:Circular) DELETE r"
    try:
        with driver.session() as session:
            result = session.run(delete_query)
            logger.info(f"Deleted {result.consume().counters.relationships_deleted} existing NEXT_VERSION relationships.")
    except Exception as e:
        logger.error(f"Error deleting existing NEXT_VERSION relationships: {e}")
        

    
    link_query = """
    MATCH (c1:Circular)
    WHERE c1.core_id IS NOT NULL AND c1.title IS NOT NULL AND c1.date IS NOT NULL
    CALL {
        WITH c1
        MATCH (c2:Circular)
        WHERE c2.core_id = c1.core_id
          AND c2.title = c1.title
          AND c2.date > c1.date
        RETURN c2 ORDER BY c2.date ASC LIMIT 1
    }
    MERGE (c1)-[r:NEXT_VERSION]->(c2)
    SET r.year = c2.date.year
    RETURN count(r) as links_created
    """
    try:
        with driver.session() as session:
            result = session.run(link_query)
            summary = result.consume()
            links_created_count = summary.counters.relationships_created
            
            logger.info(f"Successfully created {links_created_count} NEXT_VERSION relationships.")
    except Exception as e:
        logger.error(f"Failed to create NEXT_VERSION relationships: {e}")


if __name__ == "__main__":
    logger.info("--- Starting Node Creation/Update Process ---")
    driver = connect_neo4j()

    if not driver:
        logger.error("Cannot proceed without Neo4j connection. Exiting.")
        exit(1)

   
    metadata_map = fetch_metadata_map()
    
    local_pdf_paths = get_local_pdf_paths(PDF_DIR)

    if not local_pdf_paths or not metadata_map:
        logger.warning("No local PDFs found or no metadata fetched. Cannot process nodes.")
    else:
        processed_count = 0
        missing_metadata_count = 0
        for pdf_path in local_pdf_paths:
            circular_data = metadata_map.get(pdf_path)
            if circular_data:
                
                create_update_circular_node(driver, circular_data)
                processed_count += 1
                if processed_count > 0 and processed_count % 100 == 0: 
                    logger.info(f"Processed {processed_count}/{len(local_pdf_paths)} local files with metadata...")
            else:
                logger.warning(f"No metadata found in API data for local file: {pdf_path}")
                missing_metadata_count += 1

        logger.info(f"Finished node processing. Nodes processed: {processed_count}. Missing metadata: {missing_metadata_count}.")

    #
    if driver: 
        
        try:
            with driver.session() as session:
                session.run("CREATE INDEX circular_core_id IF NOT EXISTS FOR (n:Circular) ON (n.core_id)")
                session.run("CREATE INDEX circular_title IF NOT EXISTS FOR (n:Circular) ON (n.title)")
                session.run("CREATE INDEX circular_date IF NOT EXISTS FOR (n:Circular) ON (n.date)")
                logger.info("Ensured necessary indexes for linking exist.")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
        
        link_circular_versions(driver) 

    close_neo4j_driver()
    logger.info("--- Node Creation/Update and Linking Process Finished ---")
