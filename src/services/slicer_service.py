"""Slicer service for G-code generation."""

from pathlib import Path
from typing import Dict, Any, Optional

from config import get_settings
from utils import get_model_dir, run_command_async, run_command_safe


class SlicerService:
    """Service for model slicing operations."""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def slice_model(
        self,
        model_id: str,
        profile: str,
        extra_args: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Slice a model using the configured slicer CLI to generate G-code.
        
        Args:
            model_id: The model identifier
            profile: Path to slicer configuration/profile file
            extra_args: Optional dict of additional slicer arguments
            
        Returns:
            dict: Contains model_id, gcode_path, slicer_stdout, and slicer_stderr
        """
        try:
            if not self.settings.slicer_bin:
                return {
                    "error": "SLICER_BIN not configured",
                    "details": "Set the SLICER_BIN environment variable"
                }
            
            if not self.settings.openscad_bin:
                return {
                    "error": "OPENSCAD_BIN not configured",
                    "details": "OpenSCAD is required to generate STL from SCAD file"
                }
            
            mdir = get_model_dir(model_id)
            scad_path = mdir / "main.scad"
            
            if not scad_path.exists():
                return {
                    "error": "Model not found",
                    "details": f"No main.scad found for model {model_id}"
                }
            
            # Step 1: Generate STL from OpenSCAD
            stl_path = mdir / "model.stl"
            stl_result = await self._generate_stl(scad_path, stl_path, mdir)
            
            if not stl_result["success"]:
                return {
                    "error": "STL generation failed",
                    "details": stl_result["stderr"],
                    "stdout": stl_result["stdout"]
                }
            
            if not stl_path.exists():
                return {
                    "error": "STL file not generated",
                    "details": "OpenSCAD completed but no STL was created"
                }
            
            # Step 2: Slice STL to G-code
            gcode_path = mdir / "model.gcode"
            slice_result = await self._slice_to_gcode(
                stl_path, gcode_path, profile, extra_args, mdir
            )
            
            if not slice_result["success"]:
                return {
                    "error": "Slicing failed",
                    "details": slice_result["stderr"],
                    "stdout": slice_result["stdout"]
                }
            
            if not gcode_path.exists():
                return {
                    "error": "G-code not generated",
                    "details": "Slicer completed but no G-code was created"
                }
            
            return {
                "model_id": model_id,
                "gcode_path": str(gcode_path.resolve()),
                "slicer_stdout": slice_result["stdout"],
                "slicer_stderr": slice_result["stderr"]
            }
            
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {
                "error": "Failed to slice model",
                "details": str(e)
            }
    
    async def _generate_stl(
        self,
        scad_path: Path,
        stl_path: Path,
        cwd: Path
    ) -> Dict[str, Any]:
        """Generate STL from OpenSCAD file."""
        cmd = [
            self.settings.openscad_bin,
            "-o", str(stl_path),
            str(scad_path)
        ]
        
        return await run_command_async(cmd, timeout=180, cwd=cwd)
    
    async def _slice_to_gcode(
        self,
        stl_path: Path,
        gcode_path: Path,
        profile: str,
        extra_args: Optional[Dict[str, str]],
        cwd: Path
    ) -> Dict[str, Any]:
        """Slice STL to G-code."""
        cmd = [
            self.settings.slicer_bin,
            "--load", profile,
            "--output", str(gcode_path),
            str(stl_path)
        ]
        
        # Add extra arguments if provided
        if extra_args:
            for key, value in extra_args.items():
                cmd.extend([f"--{key}", value])
        
        return await run_command_async(
            cmd,
            timeout=self.settings.slice_timeout,
            cwd=cwd
        )
