# GitHub Webhook Setup Guide

This guide explains how to set up webhook notifications from GitHub Actions to your Railway app for real-time status updates.

## Overview

Webhooks allow GitHub Actions to notify your Railway app immediately when:
- A workflow starts
- A workflow completes successfully
- A workflow fails
- Individual job steps change status

## Setup Steps

### 1. Generate a Webhook Secret

First, generate a secure random secret:

```bash
# On Linux/Mac:
openssl rand -hex 32

# On Windows PowerShell:
-join ((1..32) | ForEach {'{0:X}' -f (Get-Random -Max 256)})
```

Save this secret - you'll need it for both GitHub and Railway.

### 2. Add Secret to Railway

In your Railway project:

1. Go to your project settings
2. Click on "Variables"
3. Add a new variable:
   - Name: `GITHUB_WEBHOOK_SECRET`
   - Value: [Your generated secret]

### 3. Get Your Webhook URL

Your webhook endpoint will be:
```
https://virtual-tour-generator-production.up.railway.app/api/webhook/github
```

Test that it's accessible:
```bash
curl https://virtual-tour-generator-production.up.railway.app/api/webhook/github/test
```

### 4. Configure GitHub Repository Webhook

1. Go to your GitHub repository: https://github.com/bac1876/listinghelper
2. Click "Settings" → "Webhooks" → "Add webhook"
3. Configure the webhook:
   - **Payload URL**: `https://virtual-tour-generator-production.up.railway.app/api/webhook/github`
   - **Content type**: `application/json`
   - **Secret**: [Your generated secret from step 1]
   - **Which events?**: Select "Let me select individual events"
     - Check: "Workflow runs"
     - Check: "Workflow jobs"
   - **Active**: ✓ Check this box

4. Click "Add webhook"

### 5. Verify Webhook

After adding the webhook:

1. GitHub will send a ping event
2. Check the "Recent Deliveries" tab in webhook settings
3. You should see a successful delivery (green checkmark)

## Benefits

With webhooks configured:

1. **Real-time Updates**: No more polling for status
2. **Accurate Progress**: Get immediate notification when videos are ready
3. **Error Handling**: Instant notification of failures
4. **Better UX**: Users see live progress updates

## Testing

To test the webhook integration:

1. Submit a new video job through the app
2. Watch the logs in Railway
3. You should see webhook events being received
4. The job status will update automatically

## Troubleshooting

### Webhook not receiving events

1. Check Railway logs for webhook errors
2. Verify the secret matches in both GitHub and Railway
3. Ensure the webhook URL is publicly accessible
4. Check GitHub webhook "Recent Deliveries" for errors

### Invalid signature errors

This means the secret doesn't match. Double-check:
- No extra spaces in the secret
- Same secret in GitHub and Railway
- The variable name is exactly `GITHUB_WEBHOOK_SECRET`

### Events received but job not updating

Check that:
- The job ID format matches between Railway and GitHub
- The `active_jobs` dictionary is accessible
- No errors in Railway logs when processing webhook

## Security Notes

- Always use a webhook secret in production
- The webhook endpoint validates signatures to ensure requests are from GitHub
- Don't log sensitive webhook payload data
- Rotate secrets periodically

## Current Implementation

The webhook handler (`webhook_handler.py`):
- Verifies GitHub signatures
- Updates job status in real-time
- Constructs Cloudinary URLs when workflows complete
- Handles both workflow_run and workflow_job events

Once configured, your system will have full real-time integration between GitHub Actions and your Railway app!