import os
import json
import time
import requests
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class GitHubActionsIntegration:
    def __init__(self):
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.github_owner = os.environ.get('GITHUB_OWNER')
        self.github_repo = os.environ.get('GITHUB_REPO')
        self.workflow_file = 'render-video.yml'
        
        if not all([self.github_token, self.github_owner, self.github_repo]):
            raise ValueError("Missing required GitHub environment variables: GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO")
        
        self.headers = {
            'Authorization': f'Bearer {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        self.base_url = f'https://api.github.com/repos/{self.github_owner}/{self.github_repo}'
    
    def trigger_video_render(self, images: List[str], property_details: Dict[str, Any], settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Trigger GitHub Actions workflow to render video with Remotion
        
        Args:
            images: List of image URLs
            property_details: Property information dict
            settings: Optional render settings
            
        Returns:
            Dict with job_id and status
        """
        try:
            # Generate unique job ID
            job_id = f"tour_{int(time.time())}_{os.urandom(4).hex()}"
            
            # Default settings if not provided
            if settings is None:
                settings = {
                    "durationPerImage": 8,
                    "effectSpeed": "medium",
                    "transitionDuration": 1.5
                }
            
            # Prepare workflow inputs
            workflow_inputs = {
                "ref": "main",  # Branch to run workflow on
                "inputs": {
                    "images": json.dumps(images),
                    "propertyDetails": json.dumps(property_details),
                    "settings": json.dumps(settings),
                    "jobId": job_id
                }
            }
            
            # Trigger workflow
            dispatch_url = f"{self.base_url}/actions/workflows/{self.workflow_file}/dispatches"
            response = requests.post(dispatch_url, headers=self.headers, json=workflow_inputs)
            
            if response.status_code == 204:
                logger.info(f"Successfully triggered GitHub Actions workflow for job {job_id}")
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": "workflow_triggered",
                    "message": "Video rendering started via GitHub Actions"
                }
            else:
                logger.error(f"Failed to trigger workflow: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Failed to trigger workflow: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Error triggering GitHub Actions: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of a video render job
        
        Args:
            job_id: The job ID to check
            
        Returns:
            Dict with job status and video URL if completed
        """
        try:
            # Get recent workflow runs
            runs_url = f"{self.base_url}/actions/workflows/{self.workflow_file}/runs"
            response = requests.get(runs_url, headers=self.headers)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to fetch workflow runs: {response.status_code}"
                }
            
            runs = response.json()
            
            # Find the run for this job_id
            for run in runs.get('workflow_runs', []):
                # Check if this run is for our job
                # We'll need to check the artifacts to find the matching job_id
                if run['status'] == 'completed':
                    artifacts_url = run['artifacts_url']
                    artifacts_response = requests.get(artifacts_url, headers=self.headers)
                    
                    if artifacts_response.status_code == 200:
                        artifacts = artifacts_response.json()
                        
                        for artifact in artifacts.get('artifacts', []):
                            if f"render-result-{job_id}" in artifact['name']:
                                # Found our job! Download the result
                                return self._download_job_result(artifact, run)
            
            # If we get here, job is either still running or not found
            return {
                "success": True,
                "status": "processing",
                "message": "Video is still being rendered"
            }
            
        except Exception as e:
            logger.error(f"Error checking job status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _download_job_result(self, artifact: Dict[str, Any], run: Dict[str, Any]) -> Dict[str, Any]:
        """
        Download and parse the job result artifact
        
        Args:
            artifact: The artifact data
            run: The workflow run data
            
        Returns:
            Dict with job result
        """
        try:
            # Get download URL
            download_url = f"{artifact['archive_download_url']}"
            response = requests.get(download_url, headers=self.headers, stream=True)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to download artifact: {response.status_code}"
                }
            
            # The artifact is a zip file, we need to extract and read result.json
            import zipfile
            import io
            
            try:
                with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                    # List files in the zip for debugging
                    zip_contents = zip_file.namelist()
                    logger.info(f"Artifact contents: {zip_contents}")
                    
                    if 'result.json' not in zip_contents:
                        logger.error("result.json not found in artifact")
                        return {
                            "success": False,
                            "error": "result.json not found in artifact",
                            "artifact_contents": zip_contents
                        }
                    
                    with zip_file.open('result.json') as result_file:
                        # Read raw content first for debugging
                        raw_content = result_file.read()
                        logger.info(f"Raw result.json content: {raw_content[:500]}")  # Log first 500 chars
                        
                        # Try to parse JSON
                        try:
                            result = json.loads(raw_content)
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON parsing error: {e}")
                            logger.error(f"Raw content: {raw_content}")
                            
                            # Try to extract video URL with regex as fallback
                            import re
                            video_url_match = re.search(r'"videoUrl":\s*"([^"]+)"', raw_content.decode('utf-8'))
                            if video_url_match and video_url_match.group(1) != "error:no-video-url":
                                logger.info(f"Extracted video URL via regex: {video_url_match.group(1)}")
                                return {
                                    "success": True,
                                    "status": "completed",
                                    "video_url": video_url_match.group(1),
                                    "duration": 0,
                                    "render_time": "unknown",
                                    "timestamp": "unknown",
                                    "warning": "JSON parsing failed, extracted URL via regex"
                                }
                            
                            return {
                                "success": False,
                                "error": f"Invalid JSON in result.json: {e}",
                                "raw_content": raw_content.decode('utf-8')[:500]
                            }
                        
                        # Check if it's an error response
                        if not result.get('success', True):
                            return {
                                "success": False,
                                "status": "failed",
                                "error": result.get('error', 'Unknown error in result.json'),
                                "video_url": result.get('videoUrl'),
                                "timestamp": result.get('timestamp')
                            }
                        
                        # Check for placeholder video URL
                        video_url = result.get('videoUrl', '')
                        if video_url.startswith('error:'):
                            logger.error(f"Error video URL found: {video_url}")
                            return {
                                "success": False,
                                "status": "failed",
                                "error": f"Video generation failed: {video_url}",
                                "duration": result.get('duration'),
                                "render_time": result.get('renderTime'),
                                "timestamp": result.get('timestamp')
                            }
                        
                        return {
                            "success": True,
                            "status": "completed",
                            "video_url": video_url,
                            "duration": result.get('duration'),
                            "render_time": result.get('renderTime'),
                            "timestamp": result.get('timestamp')
                        }
                        
            except zipfile.BadZipFile as e:
                logger.error(f"Invalid zip file: {e}")
                return {
                    "success": False,
                    "error": f"Invalid artifact zip file: {e}"
                }
                    
        except Exception as e:
            logger.error(f"Error downloading job result: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """
        Get the overall status of the render-video workflow
        
        Returns:
            Dict with workflow status information
        """
        try:
            workflow_url = f"{self.base_url}/actions/workflows/{self.workflow_file}"
            response = requests.get(workflow_url, headers=self.headers)
            
            if response.status_code == 200:
                workflow = response.json()
                return {
                    "success": True,
                    "workflow": {
                        "name": workflow.get('name'),
                        "state": workflow.get('state'),
                        "created_at": workflow.get('created_at'),
                        "updated_at": workflow.get('updated_at')
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get workflow status: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }