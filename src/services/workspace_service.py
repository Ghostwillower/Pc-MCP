"""Workspace service for model management."""

from typing import Dict, Any

from config import get_settings


class WorkspaceService:
    """Service for workspace and model management."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def list_models(self) -> Dict[str, Any]:
        """
        List all models in the workspace.
        
        Returns:
            dict: Contains list of models with their status
        """
        try:
            self.settings.ensure_workspace()
            models_base = self.settings.models_dir
            
            if not models_base.exists():
                return {"models": []}
            
            models = []
            for model_path in sorted(models_base.iterdir()):
                if not model_path.is_dir():
                    continue
                
                model_id = model_path.name
                
                # Check for main.scad
                scad_exists = (model_path / "main.scad").exists()
                
                # Check for gcode
                gcode_exists = (model_path / "model.gcode").exists()
                
                # Count previews
                preview_count = len(list(model_path.glob("preview_*.png")))
                
                models.append({
                    "model_id": model_id,
                    "scad_exists": scad_exists,
                    "gcode_exists": gcode_exists,
                    "previews": preview_count
                })
            
            return {"models": models}
            
        except Exception as e:
            return {
                "error": "Failed to list models",
                "details": str(e)
            }
