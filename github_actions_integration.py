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
        
        # Validate token on initialization
        self.is_valid = self.validate_token()
    
    def validate_token(self) -> bool:
        """
        Validate the GitHub token by checking repository access
        
        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Try to access the repository
            test_url = f"{self.base_url}"
            response = requests.get(test_url, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"GitHub token validated successfully for {self.github_owner}/{self.github_repo}")
                return True
            elif response.status_code == 401:
                logger.error(f"GitHub token is invalid or expired (401 Unauthorized)")
                logger.error("Please generate a new token at: https://github.com/settings/tokens")
                return False
            elif response.status_code == 404:
                logger.error(f"Repository {self.github_owner}/{self.github_repo} not found or token lacks access")
                return False
            else:
                logger.warning(f"Unexpected status code when validating token: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating GitHub token: {e}")
            return False
    
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
        # Check if token is valid before attempting to trigger
        if not self.is_valid:
            logger.error("Cannot trigger GitHub Actions - token is invalid or expired")
            return {
                "success": False,
                "error": "GitHub token is invalid or expired",
                "details": "Please update GITHUB_TOKEN in Railway environment variables with a new token from https://github.com/settings/tokens"
            }
        
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
    
    def get_workflow_status(self, job_id: str) -> str:
        """
        Get the status of a GitHub Actions workflow run by job ID
        
        Args:
            job_id: The job identifier used when triggering the workflow
            
        Returns:
            Status string: 'queued', 'in_progress', 'completed', 'failed', or 'unknown'
        """
        try:
            # Get recent workflow runs
            runs_url = f"{self.base_url}/actions/workflows/{self.workflow_file}/runs?per_page=20"
            response = requests.get(runs_url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch workflow runs: {response.status_code}")
                return 'unknown'
            
            runs = response.json()
            
            # Find the run for this job_id by checking inputs
            for run in runs.get('workflow_runs', []):
                # Check if this run matches our job ID
                # The job_id is passed as an input to the workflow
                if run.get('name', '').endswith(job_id) or job_id in run.get('display_title', ''):
                    status = run.get('status', 'unknown')
                    conclusion = run.get('conclusion', '')
                    
                    if status == 'completed':
                        if conclusion == 'success':
                            return 'completed'
                        else:
                            return 'failed'
                    elif status in ['queued', 'in_progress']:
                        return status
                    else:
                        return 'unknown'
            
            # If not found, assume it's still queued or starting
            return 'queued'
            
        except Exception as e:
            logger.error(f"Error checking workflow status: {e}")
            return 'unknown'
    
    def get_workflow_artifact(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the artifact data from a completed workflow
        
        Args:
            job_id: The job identifier
            
        Returns:
            Dict with artifact data including video URL, or None if not found
        """
        try:
            # Get recent workflow runs
            runs_url = f"{self.base_url}/actions/workflows/{self.workflow_file}/runs?per_page=10"
            response = requests.get(runs_url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch workflow runs: {response.status_code}")
                return None
            
            runs = response.json()
            
            # Find the completed run for this job_id
            for run in runs.get('workflow_runs', []):
                if run['status'] == 'completed' and run['conclusion'] == 'success':
                    # Check artifacts for this run
                    artifacts_url = run['artifacts_url']
                    artifacts_response = requests.get(artifacts_url, headers=self.headers)
                    
                    if artifacts_response.status_code == 200:
                        artifacts = artifacts_response.json()
                        
                        for artifact in artifacts.get('artifacts', []):
                            if f"render-result-{job_id}" in artifact['name']:
                                # Found our artifact, download and parse it
                                result = self._download_job_result(artifact, run)
                                if result.get('success'):
                                    return result.get('data', {})
                                    
            return None
            
        except Exception as e:
            logger.error(f"Error getting workflow artifact: {e}")
            return None
    
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
                            "data": {
                                "videoUrl": video_url,
                                "duration": result.get('duration'),
                                "renderTime": result.get('renderTime'),
                                "timestamp": result.get('timestamp')
                            },
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
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """
        Get the overall info of the render-video workflow
        
        Returns:
            Dict with workflow information
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