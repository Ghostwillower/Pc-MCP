"""Input validation utilities."""

import re


def sanitize_model_id(model_id: str) -> str:
    """
    Sanitize model_id to prevent directory traversal attacks.
    
    Args:
        model_id: The model identifier
        
    Returns:
        str: Sanitized model_id
        
    Raises:
        ValueError: If model_id contains invalid characters
    """
    # Only allow alphanumeric, hyphens, and underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', model_id):
        raise ValueError(
            f"Invalid model_id: {model_id}. "
            "Only alphanumeric, hyphens, and underscores allowed."
        )
    return model_id
