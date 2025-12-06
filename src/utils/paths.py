"""Path management utilities."""

from pathlib import Path
from functools import lru_cache

from utils.validation import sanitize_model_id
from config import get_settings


@lru_cache(maxsize=128)
def get_model_dir(model_id: str) -> Path:
    """
    Get the directory path for a specific model (cached).
    
    Using lru_cache improves performance by avoiding repeated
    path construction and validation for the same model_id.
    
    Note: Input is validated before caching to prevent cache pollution.
    The cache size is limited to 128 entries to prevent memory issues.
    
    Args:
        model_id: The model identifier (will be validated)
        
    Returns:
        Path: Absolute path to the model directory
        
    Raises:
        ValueError: If model_id is invalid
    """
    # Validation happens here - only valid IDs get cached
    sanitized_id = sanitize_model_id(model_id)
    settings = get_settings()
    return settings.models_dir / sanitized_id
