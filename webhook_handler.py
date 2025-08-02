"""
Webhook handler for GitHub Actions notifications
"""

from flask import Blueprint, request, jsonify
import hmac
import hashlib
import os
import logging
import json

logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhook', __name__, url_prefix='/api/webhook')

# Get webhook secret from environment
WEBHOOK_SECRET = os.environ.get('GITHUB_WEBHOOK_SECRET', '')

def verify_github_signature(payload_body, signature_header):
    """Verify that the webhook is from GitHub"""
    if not WEBHOOK_SECRET:
        # If no secret configured, skip verification (not recommended for production)
        return True
    
    if not signature_header:
        return False
    
    # GitHub sends the signature in the format "sha256=<signature>"
    try:
        algorithm, signature = signature_header.split('=')
        if algorithm != 'sha256':
            return False
    except ValueError:
        return False
    
    # Calculate expected signature
    mac = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = mac.hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(signature, expected_signature)

@webhook_bp.route('/github', methods=['POST'])
def github_webhook():
    """Handle GitHub Actions webhook notifications"""
    try:
        # Get the raw payload for signature verification
        payload_body = request.data
        signature_header = request.headers.get('X-Hub-Signature-256')
        
        # Verify the webhook is from GitHub
        if WEBHOOK_SECRET and not verify_github_signature(payload_body, signature_header):
            logger.warning("Invalid GitHub webhook signature")
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse the JSON payload
        payload = request.get_json()
        
        # Get the event type
        event_type = request.headers.get('X-GitHub-Event')
        
        if event_type == 'workflow_run':
            # Handle workflow run events
            workflow_run = payload.get('workflow_run', {})
            
            # Extract relevant information
            workflow_name = workflow_run.get('name')
            status = workflow_run.get('status')
            conclusion = workflow_run.get('conclusion')
            run_id = workflow_run.get('id')
            
            # Look for job ID in workflow inputs
            inputs = workflow_run.get('inputs', {})
            job_id = inputs.get('jobId')
            
            logger.info(f"Workflow {workflow_name} (run {run_id}) - Status: {status}, Conclusion: {conclusion}")
            
            if job_id:
                # Import the active_jobs from the main module
                try:
                    from working_ken_burns_github import active_jobs
                    
                    # Find the Railway job that corresponds to this GitHub job
                    railway_job_id = None
                    for rid, job_data in active_jobs.items():
                        if job_data.get('github_job_id') == job_id:
                            railway_job_id = rid
                            break
                    
                    if railway_job_id:
                        # Update job status based on workflow status
                        if status == 'completed':
                            if conclusion == 'success':
                                active_jobs[railway_job_id]['status'] = 'completed'
                                active_jobs[railway_job_id]['progress'] = 100
                                active_jobs[railway_job_id]['current_step'] = 'Video rendering complete'
                                
                                # Construct Cloudinary URL
                                cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', 'dib3kbifc')
                                video_url = f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{job_id}.mp4"
                                active_jobs[railway_job_id]['video_url'] = video_url
                                active_jobs[railway_job_id]['cloudinary_video'] = True
                                
                                logger.info(f"Job {railway_job_id} completed successfully. Video at: {video_url}")
                            else:
                                active_jobs[railway_job_id]['status'] = 'failed'
                                active_jobs[railway_job_id]['current_step'] = f'Workflow failed: {conclusion}'
                                logger.error(f"Job {railway_job_id} failed with conclusion: {conclusion}")
                        elif status == 'in_progress':
                            active_jobs[railway_job_id]['current_step'] = 'GitHub Actions rendering in progress'
                            active_jobs[railway_job_id]['progress'] = 75
                    else:
                        logger.warning(f"No Railway job found for GitHub job {job_id}")
                        
                except Exception as e:
                    logger.error(f"Error updating job status from webhook: {e}")
            
            return jsonify({'status': 'processed'}), 200
            
        elif event_type == 'workflow_job':
            # Handle individual job events
            action = payload.get('action')
            job = payload.get('workflow_job', {})
            job_name = job.get('name')
            status = job.get('status')
            
            logger.info(f"Workflow job {job_name} - Action: {action}, Status: {status}")
            
            return jsonify({'status': 'acknowledged'}), 200
            
        else:
            # Other event types
            logger.info(f"Received {event_type} event")
            return jsonify({'status': 'ignored'}), 200
            
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@webhook_bp.route('/github/test', methods=['GET'])
def test_webhook():
    """Test endpoint to verify webhook is accessible"""
    return jsonify({
        'status': 'ok',
        'webhook_configured': bool(WEBHOOK_SECRET),
        'endpoint': '/api/webhook/github'
    })