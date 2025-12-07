"""Printer service for OctoPrint integration."""

import json
from typing import Dict, Any, Optional
import httpx

from config import get_settings
from utils import get_model_dir


class PrinterService:
    """Service for 3D printer operations via OctoPrint."""
    
    def __init__(self):
        self.settings = get_settings()
        # Use httpx.AsyncClient for better performance with connection pooling
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client with connection pooling."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the 3D printer via OctoPrint.
        
        Returns:
            dict: Contains job and printer status information from OctoPrint
        """
        try:
            if not self.settings.octoprint_api_key:
                return {
                    "error": "OCTOPRINT_API_KEY not configured",
                    "details": "Set the OCTOPRINT_API_KEY environment variable"
                }
            
            job_status = await self._get("/api/job")
            printer_status = await self._get("/api/printer")
            
            return {
                "job": job_status,
                "printer": printer_status
            }
            
        except Exception as e:
            return {
                "error": "Failed to get printer status",
                "details": str(e)
            }
    
    async def upload_and_start(self, model_id: str) -> Dict[str, Any]:
        """
        Upload G-code to OctoPrint and start the print job.
        
        Args:
            model_id: The model identifier
            
        Returns:
            dict: Contains upload_result and start_result from OctoPrint
        """
        try:
            if not self.settings.octoprint_api_key:
                return {
                    "error": "OCTOPRINT_API_KEY not configured",
                    "details": "Set the OCTOPRINT_API_KEY environment variable"
                }
            
            mdir = get_model_dir(model_id)
            gcode_path = mdir / "model.gcode"
            
            if not gcode_path.exists():
                return {
                    "error": "G-code not found",
                    "details": f"No model.gcode found for model {model_id}. Run slicer_slice_model first."
                }
            
            # Upload file to OctoPrint
            filename = f"{model_id}_model.gcode"
            
            with open(gcode_path, 'rb') as f:
                files = {'file': (filename, f, 'application/octet-stream')}
                upload_result = await self._post("/api/files/local", files=files)
            
            if "error" in upload_result:
                return {
                    "model_id": model_id,
                    "upload_result": upload_result,
                    "error": "Upload failed"
                }
            
            # Start the print job
            start_payload = {
                "command": "select",
                "print": True
            }
            
            file_path = f"local/{filename}"
            start_result = await self._post(f"/api/files/{file_path}", payload=start_payload)
            
            return {
                "model_id": model_id,
                "upload_result": upload_result,
                "start_result": start_result
            }
            
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {
                "error": "Failed to upload and start print",
                "details": str(e)
            }
    
    async def send_gcode(self, gcode: str) -> Dict[str, Any]:
        """
        Send a single G-code command to the printer.
        
        Args:
            gcode: The G-code command to send
            
        Returns:
            dict: Contains sent command and result from OctoPrint
        """
        try:
            if not self.settings.octoprint_api_key:
                return {
                    "error": "OCTOPRINT_API_KEY not configured",
                    "details": "Set the OCTOPRINT_API_KEY environment variable"
                }
            
            result = await self._post(
                "/api/printer/command",
                payload={"commands": [gcode]}
            )
            
            return {
                "sent": gcode,
                "result": result
            }
            
        except Exception as e:
            return {
                "error": "Failed to send G-code",
                "details": str(e)
            }
    
    async def _get(self, path: str) -> Dict[str, Any]:
        """Make a GET request to OctoPrint API."""
        if not self.settings.octoprint_api_key:
            return {"error": "OCTOPRINT_API_KEY not configured"}
        
        try:
            url = f"{self.settings.octoprint_url.rstrip('/')}{path}"
            headers = {"X-Api-Key": self.settings.octoprint_api_key}
            
            client = await self._get_client()
            response = await client.get(url, headers=headers)
            
            if response.status_code == 204:
                return {"status": 204}
            
            if response.status_code in (200, 201):
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"status": response.status_code, "body": response.text}
            
            return {
                "error": f"HTTP {response.status_code}",
                "status": response.status_code,
                "body": response.text[:500]
            }
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    async def _post(
        self,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make a POST request to OctoPrint API."""
        if not self.settings.octoprint_api_key:
            return {"error": "OCTOPRINT_API_KEY not configured"}
        
        try:
            url = f"{self.settings.octoprint_url.rstrip('/')}{path}"
            headers = {"X-Api-Key": self.settings.octoprint_api_key}
            
            client = await self._get_client()
            
            if files:
                response = await client.post(url, headers=headers, files=files, data=payload)
            else:
                headers["Content-Type"] = "application/json"
                response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 204:
                return {"status": 204}
            
            if response.status_code in (200, 201):
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"status": response.status_code, "body": response.text}
            
            return {
                "error": f"HTTP {response.status_code}",
                "status": response.status_code,
                "body": response.text[:500]
            }
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
