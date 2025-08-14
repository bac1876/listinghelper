#!/bin/bash

# Simple test to upload images and trigger video generation

echo "Testing video generation with fallback..."
echo "========================================="

# Upload images
echo "Uploading test images..."
response=$(curl -X POST http://localhost:5000/api/virtual-tour/upload \
  -F "images=@test_images/bedroom.jpg" \
  -F "images=@test_images/DSC06537.jpg" \
  -F "images=@test_images/DSC06567.jpg" \
  -F "property_address=123 Test Street" \
  -F "property_price=500000" \
  -F "property_beds=3" \
  -F "property_baths=2" \
  -F "property_sqft=2000" \
  -F "agent_name=Test Agent" \
  -F "agent_phone=555-0123" \
  -F "agent_email=test@example.com" \
  -F "brand_name=Test Realty" \
  -F "duration=5" \
  -F "effect_speed=medium" \
  -s)

echo "Response: $response"

# Extract job_id (it's actually returned as a direct field)
job_id=$(echo "$response" | py -c "import sys, json; data = json.load(sys.stdin); print(data.get('job_id', ''))" 2>/dev/null || echo "$response" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$job_id" ]; then
    echo "Failed to get job ID!"
    exit 1
fi

echo "Job ID: $job_id"
echo ""
echo "Monitoring status..."
echo "-------------------"

# Monitor status
for i in {1..60}; do
    sleep 3
    status_response=$(curl -s "http://localhost:5000/api/virtual-tour/job/$job_id/status")
    
    status=$(echo "$status_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    progress=$(echo "$status_response" | grep -o '"progress":[0-9]*' | cut -d':' -f2)
    current_step=$(echo "$status_response" | grep -o '"current_step":"[^"]*"' | cut -d'"' -f4)
    
    echo "[$i] Status: $status | Progress: $progress% | Step: $current_step"
    
    # Check for fallback indicators
    if echo "$current_step" | grep -q "switching to local processing"; then
        echo "   >>> FALLBACK TRIGGERED: Switching to FFmpeg!"
    fi
    
    if [ "$status" = "completed" ]; then
        echo ""
        echo "✓ Video generation completed!"
        video_url=$(echo "$status_response" | grep -o '"video_url":"[^"]*"' | cut -d'"' -f4)
        echo "Video URL: $video_url"
        exit 0
    elif [ "$status" = "failed" ]; then
        echo ""
        echo "✗ Video generation failed!"
        exit 1
    fi
done

echo "Timeout waiting for completion"
exit 1