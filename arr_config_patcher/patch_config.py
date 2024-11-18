import logging
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set
from xml.dom import minidom

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def create_default_config(config_path: Path) -> ET.Element:
    """
    Creates a new XML configuration file with default structure.

    Args:
        config_path (Path): Path where the config file should be created

    Returns:
        ET.Element: Root element of the new config
    """
    logger.info(f"Creating new config file at {config_path}")
    root = ET.Element("Config")

    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write initial XML structure
    tree = ET.ElementTree(root)
    with config_path.open(mode='wb') as f:
        tree.write(f, encoding='UTF-8', xml_declaration=True)

    return root


def prettify_xml(elem: ET.Element) -> str:
    """
    Takes an ElementTree element and returns a prettified XML string.

    Args:
        elem (ET.Element): The XML element to prettify

    Returns:
        str: Prettified XML string
    """
    rough_string = ET.tostring(elem, 'UTF-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    return '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])


def add_postgres_config(config_path: Path = Path('/config/config.xml')) -> None:
    """
    Modifies XML configuration file to include PostgreSQL settings from environment variables.

    Args:
        config_path (Path): Path to the XML configuration file

    Raises:
        ET.ParseError: If the XML file is malformed
        IOError: If there are file access issues
        SystemExit: If required environment variables are missing
    """
    try:
        logger.info(f"Starting configuration update at {config_path}")

        # Check if file exists, create if it doesn't
        root: ET.Element
        if not config_path.exists():
            root = create_default_config(config_path)
            logger.info("Created new configuration file")
        else:
            try:
                tree: ET.ElementTree = ET.parse(config_path)
                root = tree.getroot()
            except ET.ParseError as e:
                logger.error(f"Error parsing existing XML file: {e}")
                logger.info("Creating new configuration file due to parse error")
                root = create_default_config(config_path)

        # Required environment variables mapping
        required_vars: Dict[str, str] = {
            'PostgresUser': 'POSTGRES_USER',
            'PostgresPassword': 'POSTGRES_PASSWORD',
            'PostgresPort': 'POSTGRES_PORT',
            'PostgresHost': 'POSTGRES_HOST',
            'PostgresMainDb': 'POSTGRES_MAIN_DB',
            'PostgresLogDb': 'POSTGRES_LOG_DB'
        }

        # Check if all environment variables exist
        missing_vars: List[str] = []
        for xml_key, env_var in required_vars.items():
            if env_var not in os.environ:
                missing_vars.append(env_var)

        if missing_vars:
            logger.error("Missing required environment variables:")
            for var in missing_vars:
                logger.error(f"- {var}")
            sys.exit(1)

        # Track which variables were modified
        modified_vars: Set[str] = set()

        # Add or update PostgreSQL configuration
        for xml_key, env_var in required_vars.items():
            env_value = os.environ[env_var]
            element: Optional[ET.Element] = root.find(xml_key)

            if element is None:
                # Create new element
                element = ET.SubElement(root, xml_key)
                element.text = env_value
                logger.info(f"Added new configuration: {xml_key}={env_value}")
                modified_vars.add(xml_key)
            else:
                # Check if value is different
                if element.text != env_value:
                    logger.info(f"Updating {xml_key}: {element.text} → {env_value}")
                    element.text = env_value
                    modified_vars.add(xml_key)
                else:
                    logger.debug(f"No change needed for {xml_key}")

        if modified_vars:
            # Convert to pretty XML and write to file
            pretty_xml: str = prettify_xml(root)
            config_path.write_text(pretty_xml, encoding='UTF-8')
            logger.info(f"Successfully updated {len(modified_vars)} configuration values")
            logger.info(f"Modified variables: {', '.join(sorted(modified_vars))}")
        else:
            logger.info("No configuration changes were necessary")

    except ET.ParseError as e:
        logger.error(f"Error parsing XML file: {e}")
        sys.exit(1)
    except IOError as e:
        logger.error(f"Error accessing file {config_path}: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.exception("Stack trace:")
        sys.exit(1)


if __name__ == "__main__":
    add_postgres_config()
