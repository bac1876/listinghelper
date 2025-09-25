import base64
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

import requests

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a creative real estate copywriter. Given a photo description and room context, "
    "produce a short narration line (1-2 sentences) that highlights the room's key selling points. "
    "Keep tone warm, descriptive, and suited for luxury property tours."
)

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"


def _encode_image(image_path: Path) -> str:
    with image_path.open('rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def _build_prompt(room_label: str, property_details: Dict[str, Any]) -> str:
    address = property_details.get('address', '')
    details1 = property_details.get('details1', '')
    details2 = property_details.get('details2', '')
    agent = property_details.get('agent_name', '')

    extras = []
    if address:
        extras.append(f"Property address: {address}.")
    if details1:
        extras.append(f"Property highlights: {details1}.")
    if details2 and details2 != details1:
        extras.append(f"Additional highlight: {details2}.")
    if agent:
        extras.append(f"Listing agent: {agent}.")

    extras.append(f"Room focus: {room_label}.")
    extras.append("Keep the narration 1-2 sentences, painting a vivid picture for buyers.")
    return " ".join(extras)


def generate_room_scripts(assignments: List[Dict[str, Any]], property_details: Dict[str, Any], job_dir: Path) -> List[str]:
    if not assignments:
        return []

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.info("OPENAI_API_KEY not configured; using heuristic scripts")
        return _generate_fallback_scripts(assignments, property_details)

    base_url = os.getenv('OPENAI_BASE_URL', DEFAULT_OPENAI_BASE_URL).rstrip('/')
    endpoint = f"{base_url}/chat/completions"
    model = os.getenv('OPENAI_SCRIPT_MODEL', DEFAULT_MODEL)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    scripts: List[str] = []
    for idx, assignment in enumerate(assignments, start=1):
        room_label = assignment.get('room_label') or assignment.get('room') or 'Room'
        saved_filename = assignment.get('saved_filename')
        image_path = job_dir / saved_filename if saved_filename else None
        if not image_path or not image_path.exists():
            logger.warning("Image path missing for assignment %s; using fallback", assignment)
            scripts.append(_fallback_line(idx, room_label, property_details))
            continue

        try:
            image_base64 = _encode_image(image_path)
            prompt = _build_prompt(room_label, property_details)
            logger.debug("Requesting AI script for %s", room_label)

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                            },
                        ],
                    },
                ],
                "max_tokens": 180,
            }

            response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            text = _extract_text(data)
            if not text:
                logger.warning("Empty AI response for %s; using fallback", room_label)
                text = _fallback_line(idx, room_label, property_details)
            scripts.append(text)
        except Exception as exc:  # noqa: BLE001
            logger.error("AI script generation failed for %s: %s", room_label, exc)
            scripts.append(_fallback_line(idx, room_label, property_details))
    return scripts


def _extract_text(data: Dict[str, Any]) -> str:
    try:
        message = data["choices"][0]["message"]
        content = message.get("content")
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            return " ".join(parts).strip()
        if isinstance(content, str):
            return content.strip()
    except (KeyError, IndexError, TypeError) as exc:
        logger.warning("Unexpected OpenAI response format: %s (%s)", data, exc)
    return ""


def _fallback_line(index: int, room_label: str, property_details: Dict[str, Any]) -> str:
    address = property_details.get('address', '').split('\n')[0]
    return f"Scene {index}: Highlight the {room_label.lower()} at {address or 'this property'}, focusing on its best features."


def _generate_fallback_scripts(assignments: List[Dict[str, Any]], property_details: Dict[str, Any]) -> List[str]:
    return [
        _fallback_line(idx, assignment.get('room_label') or assignment.get('room') or 'Room', property_details)
        for idx, assignment in enumerate(assignments, start=1)
    ]
