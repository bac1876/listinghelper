"""
Test the new Creatomate template directly to see what it produces
"""
import requests
import json
import time

def test_template(template_id, template_name):
    """Test a template with minimal modifications"""
    
    api_key = "561802cc18514993874255b2dc4fcd1d0150ff961f26aab7d0aee02464704eac33aa94e133e90fa1bb8ac2742c165ab3"
    
    # Use example images from Creatomate for testing
    test_images = [
        "https://creatomate.com/files/assets/ef8fe36b-2e81-4495-abe8-9d6d2e8c8f1e",
        "https://creatomate.com/files/assets/e49499d0-f8a2-4d3d-aca5-29d43a655ac7",
        "https://creatomate.com/files/assets/6dc8d8be-e648-41a6-9244-bcce4274e30d",
        "https://creatomate.com/files/assets/7e81c571-7d2c-46b4-b261-919679bb41b5"
    ]
    
    # Build modifications based on template
    modifications = {}
    
    if template_name == "new":
        # New template uses Video-1 through Video-4
        for i in range(1, 5):
            modifications[f"Video-{i}.source"] = test_images[i-1]
        modifications.update({
            "Description.text": "Test Property\nLos Angeles, CA",
            "Subtext.text": "Just Listed",
            "Name.text": "Test Agent",
            "Email.text": "test@example.com",
            "Phone-Number.text": "(555) 123-4567",
            "Brand-Name.text": "Test Realty"
        })
    else:
        # Original template uses Photo-1 through Photo-5
        for i in range(1, 5):
            modifications[f"Photo-{i}.source"] = test_images[i-1]
        modifications[f"Photo-5.source"] = test_images[3]  # Repeat last image
        modifications.update({
            "Address.text": "Test Property\nLos Angeles, CA",
            "Details-1.text": "3 Beds\n2 Baths\n2000 sqft",
            "Details-2.text": "Just Listed\n$500,000",
            "Name.text": "Test Agent",
            "Email.text": "test@example.com",
            "Phone-Number.text": "(555) 123-4567",
            "Brand-Name.text": "Test Realty"
        })
    
    # Make API request
    print(f"\nTesting {template_name} template: {template_id}")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "template_id": template_id,
        "modifications": modifications
    }
    
    print("Sending request...")
    response = requests.post(
        "https://api.creatomate.com/v1/renders",
        headers=headers,
        json=data
    )
    
    if response.status_code in [200, 201, 202]:
        result = response.json()
        if isinstance(result, list):
            render_id = result[0]['id']
        else:
            render_id = result['id']
        
        print(f"Render created! ID: {render_id}")
        print("Waiting for completion...")
        
        # Poll for completion
        for i in range(30):  # Wait up to 60 seconds
            time.sleep(2)
            status_response = requests.get(
                f"https://api.creatomate.com/v1/renders/{render_id}",
                headers=headers
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get('status', 'unknown')
                progress = status_data.get('progress', 0)
                
                print(f"Status: {status} - Progress: {progress}%")
                
                if status == 'succeeded':
                    video_url = status_data.get('url', 'No URL')
                    print(f"\nVideo ready! URL: {video_url}")
                    return video_url
                elif status == 'failed':
                    print("Render failed!")
                    return None
        
        print("Timeout waiting for render")
        return None
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

# Test both templates
print("CREATOMATE TEMPLATE COMPARISON TEST")
print("="*60)

# Test new template
new_url = test_template("31b06afe-9073-4f68-a329-0e910a8be6a7", "new")

# Test original template
original_url = test_template("5c2eca01-84b8-4302-bad2-9189db4dae70", "original")

print("\n" + "="*60)
print("RESULTS:")
print(f"New template video: {new_url}")
print(f"Original template video: {original_url}")
print("\nCompare both videos to see the difference in animations!")