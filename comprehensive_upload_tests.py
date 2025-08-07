"""
Comprehensive upload tests using Playwright to identify failure patterns
Tests various scenarios with real images to understand when and why uploads fail
"""
import os
import sys
import time
import json
import psutil
import subprocess
import threading
from datetime import datetime

# Test results storage
test_results = []
server_process = None

def start_server():
    """Start the Flask server in background"""
    global server_process
    print("Starting Flask server...")
    server_process = subprocess.Popen(
        [sys.executable, 'main.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(5)  # Wait for server to start
    print("Server started")

def stop_server():
    """Stop the Flask server"""
    global server_process
    if server_process:
        server_process.terminate()
        server_process.wait()
        print("Server stopped")

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def load_test_images():
    """Load the list of test images"""
    images = []
    
    # First try to load from our downloaded images
    if os.path.exists('real_test_images/image_list.txt'):
        with open('real_test_images/image_list.txt', 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) == 3:
                    name, path, size = parts
                    if os.path.exists(path):
                        images.append({
                            'name': name,
                            'path': path,
                            'size': float(size)
                        })
    
    # Fallback to any existing test images
    if not images:
        print("No downloaded images found, using fallback images...")
        test_dirs = ['test_images', 'test-images', 'real_test_images']
        for test_dir in test_dirs:
            if os.path.exists(test_dir):
                for file in os.listdir(test_dir):
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        path = os.path.join(test_dir, file)
                        size = os.path.getsize(path) / (1024 * 1024)
                        images.append({
                            'name': file,
                            'path': path,
                            'size': size
                        })
    
    print(f"Loaded {len(images)} test images")
    return images

def run_playwright_test(test_name, image_paths, test_config={}):
    """Run a single test using Playwright"""
    print(f"\n{'='*60}")
    print(f"Running Test: {test_name}")
    print(f"Images: {len(image_paths)}")
    print(f"Config: {test_config}")
    print(f"{'='*60}")
    
    start_time = time.time()
    start_memory = get_memory_usage()
    
    result = {
        'test_name': test_name,
        'image_count': len(image_paths),
        'start_time': datetime.now().isoformat(),
        'config': test_config,
        'success': False,
        'error': None,
        'metrics': {}
    }
    
    try:
        # Create a test script for Playwright
        test_script = f'''
const {{ chromium }} = require('playwright');

(async () => {{
    const browser = await chromium.launch({{ headless: false }});
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Enable console logging
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR:', err));
    
    try {{
        // Navigate to the app
        await page.goto('http://localhost:5000', {{ timeout: 30000 }});
        console.log('Navigated to app');
        
        // Wait for page to load
        await page.waitForTimeout(2000);
        
        // File input exists but may be hidden, check for it
        const fileInput = await page.$('#file-input');
        if (!fileInput) {{
            throw new Error('File input not found');
        }}
        
        // Upload images
        const imageFiles = {json.dumps(image_paths)};
        await page.setInputFiles('#file-input', imageFiles);
        console.log('Files selected:', imageFiles.length);
        
        // Wait for images to be processed
        await page.waitForTimeout(2000);
        
        // Fill in required fields (using correct IDs)
        await page.fill('#property-address', 'Test Property {test_name}');
        await page.fill('#agent-name', 'Test Agent');
        await page.fill('#agent-phone', '555-1234');
        
        // Click generate button
        await page.click('#generate-btn');
        console.log('Generate button clicked');
        
        // Wait for processing to complete (max 2 minutes)
        let completed = false;
        let attempts = 0;
        const maxAttempts = 120;
        
        while (!completed && attempts < maxAttempts) {{
            await page.waitForTimeout(1000);
            attempts++;
            
            // Check if results section appears (success or error)
            const resultsSection = await page.$('#results-section');
            const resultsVisible = resultsSection && await resultsSection.isVisible();
            
            if (resultsVisible) {{
                // Check if it's success or error
                const hasError = await resultsSection.evaluate(el => el.classList.contains('error'));
                
                if (hasError) {{
                    const errorMessage = await page.$eval('#results-message', el => el.textContent);
                    console.log('ERROR:', errorMessage);
                    break;
                }} else {{
                    completed = true;
                    console.log('SUCCESS: Video generation completed');
                    
                    // Try to find and test the download button
                    const downloadBtn = await page.$('#download-btn');
                    if (downloadBtn) {{
                        const onclick = await downloadBtn.getAttribute('onclick');
                        console.log('Download button found with onclick:', onclick);
                        
                        // Extract job ID from onclick if present
                        const jobIdMatch = onclick ? onclick.match(/downloadVideo\\('([^']+)'\\)/) : null;
                        if (jobIdMatch) {{
                            const jobId = jobIdMatch[1];
                            const downloadUrl = 'http://localhost:5000/download/' + jobId;
                            const response = await page.request.get(downloadUrl);
                            console.log('Download response status:', response.status());
                            const contentType = response.headers()['content-type'];
                            console.log('Download response type:', contentType);
                            
                            // Check if it's actually a video
                            if (contentType && contentType.includes('video')) {{
                                console.log('VERIFIED: Video download successful');
                            }} else {{
                                console.log('WARNING: Download returned non-video content');
                            }}
                        }}
                    }}
                    break;
                }}
            }}
            
            // Check progress
            const progressText = await page.$eval('#status-message', el => el.textContent).catch(() => null);
            if (progressText && attempts % 10 === 0) {{
                console.log('Progress:', progressText);
            }}
        }}
        
        if (!completed) {{
            console.log('TIMEOUT: Processing did not complete in 2 minutes');
        }}
        
    }} catch (error) {{
        console.error('Test failed:', error);
        process.exit(1);
    }} finally {{
        await browser.close();
    }}
    
    process.exit(0);
}})();
        '''
        
        # Write test script
        script_path = f'test_script_{test_name.replace(" ", "_")}.js'
        with open(script_path, 'w') as f:
            f.write(test_script)
        
        # Run the test
        print(f"Executing Playwright test...")
        test_process = subprocess.run(
            ['node', script_path],
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout
        )
        
        # Parse results
        output = test_process.stdout + test_process.stderr
        print(f"Test output:\n{output[:1000]}...")  # Print first 1000 chars
        
        # Check for success
        if 'SUCCESS: Video generation completed' in output:
            result['success'] = True
            # Also check if video download was verified
            if 'VERIFIED: Video download successful' in output:
                print(f"[PASS] Test PASSED - Video generated and download verified")
            elif 'WARNING: Download returned non-video content' in output:
                result['success'] = False
                result['error'] = 'Video generated but download returned non-video content (likely JSON/HTML)'
                print(f"[FAIL] Test FAILED: {result['error']}")
            else:
                print(f"[PASS] Test PASSED - Video generated")
        else:
            result['success'] = False
            if 'TIMEOUT' in output:
                result['error'] = 'Timeout - processing did not complete'
            elif 'ERROR' in output:
                # Extract error message
                for line in output.split('\n'):
                    if 'ERROR:' in line:
                        result['error'] = line.split('ERROR:')[1].strip()
                        break
            else:
                result['error'] = 'Unknown failure'
            print(f"[FAIL] Test FAILED: {result['error']}")
        
        # Clean up script
        os.remove(script_path)
        
    except subprocess.TimeoutExpired:
        result['error'] = 'Test timeout (3 minutes)'
        print(f"[TIMEOUT] Test TIMEOUT")
    except Exception as e:
        result['error'] = str(e)
        print(f"[ERROR] Test ERROR: {e}")
    
    # Record metrics
    end_time = time.time()
    end_memory = get_memory_usage()
    
    result['metrics'] = {
        'duration_seconds': end_time - start_time,
        'memory_start_mb': start_memory,
        'memory_end_mb': end_memory,
        'memory_increase_mb': end_memory - start_memory
    }
    
    print(f"Duration: {result['metrics']['duration_seconds']:.2f}s")
    print(f"Memory increase: {result['metrics']['memory_increase_mb']:.2f} MB")
    
    test_results.append(result)
    return result

def run_all_tests():
    """Run all 10 test scenarios"""
    print("\n" + "="*80)
    print("COMPREHENSIVE UPLOAD TESTING")
    print("="*80)
    
    # Load test images
    images = load_test_images()
    
    if len(images) < 12:
        print(f"WARNING: Only {len(images)} images available, some tests may be limited")
    
    # Start the server
    start_server()
    
    try:
        # Test 1: Small batch (3 images)
        if len(images) >= 3:
            run_playwright_test(
                "Small Batch 3 Images",
                [img['path'] for img in images[:3]]
            )
            time.sleep(5)  # Wait between tests
        
        # Test 2: Medium batch (6 images)
        if len(images) >= 6:
            run_playwright_test(
                "Medium Batch 6 Images",
                [img['path'] for img in images[:6]]
            )
            time.sleep(5)
        
        # Test 3: Large batch (10 images)
        if len(images) >= 10:
            run_playwright_test(
                "Large Batch 10 Images",
                [img['path'] for img in images[:10]]
            )
            time.sleep(5)
        
        # Test 4: Maximum batch (12 images) - Reproduce user's issue
        if len(images) >= 12:
            run_playwright_test(
                "Maximum Batch 12 Images",
                [img['path'] for img in images[:12]],
                {'description': 'Reproducing reported failure'}
            )
            time.sleep(5)
        
        # Test 5: Large files only
        large_images = sorted(images, key=lambda x: x['size'], reverse=True)[:5]
        if large_images:
            run_playwright_test(
                "Large Files Test",
                [img['path'] for img in large_images],
                {'total_size_mb': sum(img['size'] for img in large_images)}
            )
            time.sleep(5)
        
        # Test 6: Many small files
        small_images = sorted(images, key=lambda x: x['size'])[:8]
        if len(small_images) >= 8:
            run_playwright_test(
                "Many Small Files",
                [img['path'] for img in small_images],
                {'total_size_mb': sum(img['size'] for img in small_images)}
            )
            time.sleep(5)
        
        # Test 7: Single very large file
        if images:
            largest = max(images, key=lambda x: x['size'])
            run_playwright_test(
                "Single Large File",
                [largest['path']],
                {'file_size_mb': largest['size']}
            )
            time.sleep(5)
        
        # Test 8: Incremental test (4, then 4 more)
        if len(images) >= 8:
            print("\nIncremental test - First batch...")
            run_playwright_test(
                "Incremental First 4",
                [img['path'] for img in images[:4]]
            )
            time.sleep(2)
            print("Incremental test - Second batch...")
            run_playwright_test(
                "Incremental Next 4",
                [img['path'] for img in images[4:8]]
            )
            time.sleep(5)
        
        # Test 9: Stress test - All available images
        if len(images) > 12:
            run_playwright_test(
                f"Stress Test All {len(images)} Images",
                [img['path'] for img in images],
                {'warning': 'This may fail due to limits'}
            )
            time.sleep(5)
        
        # Test 10: Recovery test - Run after potential failure
        print("\nRecovery test - Testing if server recovered...")
        if len(images) >= 3:
            run_playwright_test(
                "Recovery Test 3 Images",
                [img['path'] for img in images[:3]],
                {'description': 'Testing server recovery after stress'}
            )
        
    finally:
        # Stop the server
        stop_server()
    
    # Generate report
    generate_report()

def generate_report():
    """Generate a detailed report of test results"""
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    # Summary statistics
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r['success'])
    failed_tests = total_tests - passed_tests
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
    
    # Detailed results
    print("\nDetailed Results:")
    print("-" * 60)
    
    for result in test_results:
        status = "[PASS]" if result['success'] else "[FAIL]"
        print(f"\n{status} - {result['test_name']}")
        print(f"  Images: {result['image_count']}")
        print(f"  Duration: {result['metrics']['duration_seconds']:.2f}s")
        print(f"  Memory: {result['metrics']['memory_increase_mb']:.2f} MB increase")
        if result['error']:
            print(f"  Error: {result['error']}")
    
    # Failure analysis
    print("\n" + "="*60)
    print("FAILURE ANALYSIS")
    print("="*60)
    
    # Find patterns
    failed_results = [r for r in test_results if not r['success']]
    if failed_results:
        # Check image count correlation
        avg_failed_images = sum(r['image_count'] for r in failed_results) / len(failed_results)
        print(f"\nAverage image count in failed tests: {avg_failed_images:.1f}")
        
        # Check memory correlation
        high_memory_failures = [r for r in failed_results if r['metrics']['memory_increase_mb'] > 100]
        if high_memory_failures:
            print(f"Failures with high memory usage (>100MB): {len(high_memory_failures)}")
        
        # Common errors
        error_types = {}
        for r in failed_results:
            error = r['error'] or 'Unknown'
            error_types[error] = error_types.get(error, 0) + 1
        
        print("\nError types:")
        for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {error}: {count} occurrences")
    
    # Recommendations
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    # Find maximum reliable batch size
    passed_counts = [r['image_count'] for r in test_results if r['success']]
    if passed_counts:
        max_reliable = max(passed_counts)
        print(f"\n[OK] Maximum reliable batch size: {max_reliable} images")
    
    # Memory recommendations
    memory_increases = [r['metrics']['memory_increase_mb'] for r in test_results]
    avg_memory_per_image = sum(memory_increases) / sum(r['image_count'] for r in test_results)
    print(f"[OK] Average memory per image: {avg_memory_per_image:.2f} MB")
    
    # Time recommendations
    successful_times = [(r['metrics']['duration_seconds'], r['image_count']) 
                       for r in test_results if r['success'] and r['image_count'] > 0]
    if successful_times:
        avg_time_per_image = sum(t/c for t, c in successful_times) / len(successful_times)
        print(f"[OK] Average processing time per image: {avg_time_per_image:.2f} seconds")
    
    # Save detailed report
    report_path = 'test_results_comprehensive.json'
    with open(report_path, 'w') as f:
        json.dump({
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'timestamp': datetime.now().isoformat()
            },
            'results': test_results
        }, f, indent=2)
    
    print(f"\n[OK] Detailed report saved to: {report_path}")

if __name__ == "__main__":
    print("Starting comprehensive upload tests...")
    print("This will take several minutes to complete.")
    
    # First ensure we have test images
    if not os.path.exists('real_test_images/image_list.txt'):
        print("\nDownloading test images first...")
        os.system(f"{sys.executable} download_dropbox_images.py")
    
    # Check if we have playwright installed
    try:
        subprocess.run(['node', '--version'], capture_output=True, check=True, shell=True)
        subprocess.run(['npx', 'playwright', '--version'], capture_output=True, check=True, shell=True)
    except Exception as e:
        print(f"\nWARNING: Could not verify Node.js/Playwright: {e}")
        print("Attempting to continue anyway...")
        # Don't exit, try to run tests anyway
    
    # Run the tests
    run_all_tests()
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)