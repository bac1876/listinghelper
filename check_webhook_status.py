#!/usr/bin/env python3
"""
Check if webhooks are configured and working
"""

import requests

# Railway app URL
app_url = "https://virtual-tour-generator-production.up.railway.app"

print("Checking webhook configuration...")

# Check webhook test endpoint
webhook_test_url = f"{app_url}/api/webhook/github/test"

try:
    response = requests.get(webhook_test_url)
    
    if response.status_code == 200:
        data = response.json()
        print("\nWebhook endpoint status:")
        print(f"- Status: {data.get('status')}")
        print(f"- Webhook configured: {data.get('webhook_configured')}")
        print(f"- Endpoint: {data.get('endpoint')}")
        
        if data.get('webhook_configured'):
            print("\nWebhooks are configured in the app!")
            print("\nTo complete webhook setup:")
            print("1. Go to: https://github.com/bac1876/listinghelper/settings/hooks")
            print("2. Add webhook URL: " + app_url + data.get('endpoint'))
            print("3. Set content type to: application/json")
            print("4. Add secret from Railway env var GITHUB_WEBHOOK_SECRET")
            print("5. Select events: Workflow runs, Workflow jobs")
        else:
            print("\nWebhooks NOT configured!")
            print("Add GITHUB_WEBHOOK_SECRET to Railway environment variables")
    else:
        print(f"Webhook endpoint not found: {response.status_code}")
        print("The webhook handler may not be registered")
        
except Exception as e:
    print(f"Error checking webhook: {e}")

print("\n\nWithout webhooks, the app relies on polling to check GitHub Actions status.")
print("This can lead to delays and timeouts if rendering takes too long.")
print("\nWith webhooks configured, status updates are instant when GitHub Actions completes.")