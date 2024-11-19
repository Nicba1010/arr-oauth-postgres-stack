import logging
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set
from xml.dom import minidom

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def create_default_config(config_path: Path) -> ET.Element:
    logger.info(f"Creating new config file at {config_path}")
    root = ET.Element("Config")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(root)
    with config_path.open(mode='wb') as f:
        tree.write(f, encoding='UTF-8', xml_declaration=True)
    return root

def prettify_xml(elem: ET.Element) -> str:
    rough_string = ET.tostring(elem, 'UTF-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    return '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])

def convert_env_to_xml_key(env_var: str) -> str:
    """Convert PATCH_XXX_YYY to XxxYyy format."""
    if not env_var.startswith('PATCH_'):
        return env_var

    parts = env_var.replace('PATCH_', '').split('_')
    return ''.join(part.capitalize() for part in parts)

def patch_config(config_path: Path = Path('/config/config.xml')) -> None:
    try:
        logger.info(f"Starting configuration update at {config_path}")

        root: ET.Element
        if not config_path.exists():
            root = create_default_config(config_path)
        else:
            try:
                tree: ET.ElementTree = ET.parse(config_path)
                root = tree.getroot()
            except ET.ParseError as e:
                logger.error(f"Error parsing existing XML file: {e}")
                root = create_default_config(config_path)

        # Get all PATCH_ environment variables
        patch_vars: Dict[str, str] = {
            convert_env_to_xml_key(key): value
            for key, value in os.environ.items()
            if key.startswith('PATCH_')
        }

        if not patch_vars:
            logger.info("No PATCH_ environment variables found")
            return

        modified_vars: Set[str] = set()

        for xml_key, env_value in patch_vars.items():
            element: Optional[ET.Element] = root.find(xml_key)

            if element is None:
                element = ET.SubElement(root, xml_key)
                element.text = env_value
                logger.info(f"Added new configuration: {xml_key}={env_value}")
                modified_vars.add(xml_key)
            elif element.text != env_value:
                logger.info(f"Updating {xml_key}: {element.text} → {env_value}")
                element.text = env_value
                modified_vars.add(xml_key)
            else:
                logger.debug(f"No change needed for {xml_key}")

        if modified_vars:
            pretty_xml: str = prettify_xml(root)
            config_path.write_text(pretty_xml, encoding='UTF-8')
            logger.info(f"Successfully updated {len(modified_vars)} configuration values")
            logger.info(f"Modified variables: {', '.join(sorted(modified_vars))}")
        else:
            logger.info("No configuration changes were necessary")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.exception("Stack trace:")
        sys.exit(1)

if __name__ == "__main__":
    patch_config()