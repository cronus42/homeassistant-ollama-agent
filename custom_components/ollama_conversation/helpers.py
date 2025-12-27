"""Helper functions for entity management and system prompt generation."""
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.area_registry import async_get as async_get_area_registry
from homeassistant.components.homeassistant.exposed_entities import async_should_expose
from homeassistant.components import conversation

_LOGGER = logging.getLogger(__name__)


async def async_get_exposed_entities(hass: HomeAssistant) -> Dict[str, Dict[str, Any]]:
    """Get all entities exposed to conversation domain.
    
    Returns a dict mapping entity_id to entity attributes including:
    - friendly_name: Human-readable name
    - state: Current state
    - area_name: Area the entity belongs to (if any)
    - domain: Entity domain (light, climate, etc)
    """
    entity_states: Dict[str, Dict[str, Any]] = {}
    entity_registry = async_get_entity_registry(hass)
    device_registry = async_get_device_registry(hass)
    area_registry = async_get_area_registry(hass)

    for state in hass.states.async_all():
        # Check if entity is exposed to conversation
        if not async_should_expose(hass, conversation.DOMAIN, state.entity_id):
            continue

        # Get entity and device info
        entity = entity_registry.async_get(state.entity_id)
        device = None
        if entity and entity.device_id:
            device = device_registry.async_get(entity.device_id)

        # Build attributes dict
        attributes = dict(state.attributes)
        attributes["state"] = state.state
        attributes["domain"] = state.domain

        # Add unit of measurement to state if present
        if entity and entity.unit_of_measurement:
            attributes["state"] = f"{state.state} {entity.unit_of_measurement}"

        # Get friendly name
        if entity and entity.name:
            attributes["friendly_name"] = entity.name
        else:
            attributes["friendly_name"] = state.attributes.get("friendly_name", state.entity_id)

        # Get area info (prefer device area over entity area)
        area_name = None
        area_id = None
        
        if device and device.area_id:
            area_id = device.area_id
        elif entity and entity.area_id:
            area_id = entity.area_id

        if area_id:
            area = area_registry.async_get_area(area_id)
            if area:
                area_name = area.name
                attributes["area_name"] = area_name
                attributes["area_id"] = area_id

        entity_states[state.entity_id] = attributes

    return entity_states


def format_entities_for_prompt(entities: Dict[str, Dict[str, Any]]) -> str:
    """Format exposed entities into a readable string for the system prompt.
    
    Groups entities by domain and includes their current state and location.
    """
    if not entities:
        return "No devices are currently exposed to the assistant."

    # Group entities by domain
    entities_by_domain: Dict[str, list] = {}
    for entity_id, attrs in sorted(entities.items()):
        domain = attrs.get("domain", "unknown")
        if domain not in entities_by_domain:
            entities_by_domain[domain] = []
        entities_by_domain[domain].append((entity_id, attrs))

    # Format output
    lines = []
    lines.append("Available Smart Home Devices:")
    lines.append("")

    domain_names = {
        "light": "Lights",
        "climate": "Climate Control",
        "switch": "Switches",
        "fan": "Fans",
        "cover": "Covers (Blinds, Shutters)",
        "sensor": "Sensors",
        "binary_sensor": "Binary Sensors",
        "media_player": "Media Players",
        "lock": "Locks",
    }

    for domain in sorted(entities_by_domain.keys()):
        domain_display = domain_names.get(domain, domain.title())
        lines.append(f"**{domain_display}:**")
        
        for entity_id, attrs in entities_by_domain[domain]:
            friendly_name = attrs.get("friendly_name", entity_id)
            state = attrs.get("state", "unknown")
            area = attrs.get("area_name")
            
            if area:
                lines.append(f"  - {entity_id} ({friendly_name}) in {area}: {state}")
            else:
                lines.append(f"  - {entity_id} ({friendly_name}): {state}")
        
        lines.append("")

    return "\n".join(lines)
