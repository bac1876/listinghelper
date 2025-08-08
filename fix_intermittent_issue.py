"""
Fix for intermittent GitHub Actions failures
"""

print("""
INTERMITTENT FAILURE DIAGNOSIS
==============================

Based on your description (works once, then fails), here are the likely causes:

1. GITHUB ACTIONS CONCURRENCY LIMIT
   - GitHub Actions has limits on concurrent workflow runs
   - If a previous job is still running, new ones may queue or fail
   
2. CLOUDINARY UPLOAD TIMING
   - The video might still be processing when checked
   - Polling might timeout before video is ready

3. JOB STATE MANAGEMENT
   - The job tracking dictionary might have stale data
   - Previous job IDs might be interfering

SOLUTIONS TO IMPLEMENT:
======================

1. Check if previous workflows are still running:
   Run: python check_github_actions.py
   
2. Increase polling timeout for Cloudinary
   - Currently polls for 5 minutes (30 * 10 seconds)
   - May need to increase for larger videos

3. Add cleanup for old jobs
   - Clear completed jobs from memory after download
   
4. Add workflow status check before triggering new ones
   - Check if any workflows are in_progress
   - Queue or delay if needed

5. Add retry logic for GitHub Actions trigger
   - If trigger fails, retry with exponential backoff
   
Would you like me to implement these fixes?
""")