#!/usr/bin/env python3
"""
Apply Download Fixes
This script helps apply the enhanced download endpoint to working_ken_burns.py
"""

import os
import shutil
from datetime import datetime

print("""
========================================
Apply Download Enhancement Fixes
========================================

This script will:
1. Backup the current working_ken_burns.py
2. Show you where to add the enhanced download code
3. Provide instructions for testing

""")

# Create backup
backup_name = f"working_ken_burns_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
try:
    shutil.copy("working_ken_burns.py", backup_name)
    print(f"✅ Created backup: {backup_name}")
except Exception as e:
    print(f"⚠️ Could not create backup: {e}")
    proceed = input("\nProceed without backup? (y/n): ")
    if proceed.lower() != 'y':
        exit()

print("""
INSTRUCTIONS TO APPLY FIXES:
============================

1. Open working_ken_burns.py in your editor

2. Find the download_file function (around line 417)

3. Replace the entire function with the enhanced version from enhanced_download_endpoint.py

4. Add the new diagnostics endpoint after the download function

5. Make sure to keep these imports at the top:
   - from datetime import datetime (if not already present)

6. Save the file

KEY IMPROVEMENTS ADDED:
- Detailed request logging with unique request IDs
- File existence validation with retries
- Empty file detection
- Progress checking for in-process jobs
- Cloudinary fallback information
- Detailed error responses
- Diagnostics endpoint for troubleshooting

TESTING THE FIXES:
==================

1. Start your Flask app:
   py main.py

2. Run the download test tool:
   py test_download_functionality.py

3. Test with a recent job ID to verify:
   - Downloads work correctly
   - Error messages are descriptive
   - Diagnostics provide useful info

4. For Railway deployment:
   - Commit the changes
   - Push to your repository
   - Railway will auto-deploy
   - Test with the Railway URL

MONITORING IMPROVEMENTS:
========================

After deploying, the enhanced logging will show:
- [request_id] prefixed log entries
- Download success/failure with timing
- File sizes and types
- Detailed error context

Use the Railway log analyzer to parse these logs:
   py analyze_railway_logs.py

""")

# Check if user wants to see the diff
show_diff = input("\nWould you like to see the key changes? (y/n): ")
if show_diff.lower() == 'y':
    print("""
KEY CHANGES IN ENHANCED VERSION:
================================

1. Request tracking:
   request_id = f"{job_id}_{file_type}_{int(start_time)}"
   
2. Enhanced logging:
   logger.info(f"[{request_id}] Download request received...")
   
3. Retry logic:
   for attempt in range(max_retries):
       if os.path.exists(filepath):
           # Send file
       else:
           # Retry with delay
           
4. Empty file detection:
   if file_size == 0:
       logger.error(f"File exists but is empty")
       
5. Cloudinary fallback:
   if job_data.get('cloudinary_video'):
       error_response['cloudinary_url'] = ...
       
6. Diagnostics endpoint:
   @virtual_tour_bp.route('/download/<job_id>/diagnostics')
   def download_diagnostics(job_id):
       # Returns detailed job and file info
""")

print("""
NEXT STEPS:
===========
1. Apply the changes to working_ken_burns.py
2. Test locally with test_download_functionality.py
3. Commit and push to deploy to Railway
4. Monitor Railway logs for any download errors
5. Use analyze_railway_logs.py to parse error patterns

Good luck! 🚀
""")