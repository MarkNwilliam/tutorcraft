# json_cleaner.py
import re

def remove_pango_markup(text):
    """Remove Pango Markup tags from a string."""
    if not isinstance(text, str):
        return text
    # Remove Pango Markup tags like <b>, <i>, etc.
    return re.sub(r'<[^>]+>', '', text)

def clean_json(json_data, scene_types_to_clean=None):
    """
    Recursively clean Pango Markup from specific fields in the JSON for specified scene types.
    
    Args:
        json_data (dict or list): The JSON data to clean.
        scene_types_to_clean (list): List of scene types to clean. If None, no filtering is applied.
    """
    if isinstance(json_data, dict):
        # Check if this is a scene and if its type matches the ones to clean
        if 'type' in json_data and (scene_types_to_clean is None or json_data['type'] in scene_types_to_clean):
            for key, value in json_data.items():
                # Clean specific fields for the matching scene types
                if key in ['main_text', 'subtitle', 'text', 'voiceover', 'event', 'narration']:
                    json_data[key] = remove_pango_markup(value)
        else:
            # Recursively clean nested dictionaries
            for key, value in json_data.items():
                clean_json(value, scene_types_to_clean)
    elif isinstance(json_data, list):
        # Recursively clean each item in the list
        for item in json_data:
            clean_json(item, scene_types_to_clean)
    return json_data