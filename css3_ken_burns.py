"""
CSS3 Ken Burns Slideshow Generator
Creates professional virtual tours using pure CSS3 animations
No dependencies, instant results, works everywhere
"""

import os
import shutil
import base64
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def create_css3_ken_burns_slideshow(image_paths, job_dir, job_id, title="Property Virtual Tour"):
    """
    Create a professional CSS3 Ken Burns slideshow
    Returns the path to the generated HTML file
    """
    
    slideshow_path = os.path.join(job_dir, f'virtual_tour_{job_id}.html')
    
    # Process and optimize images
    processed_images = []
    for i, img_path in enumerate(image_paths):
        try:
            # Create web-optimized version
            web_name = f'slide_{i:03d}.jpg'
            web_path = os.path.join(job_dir, web_name)
            
            # Optimize image for web
            with Image.open(img_path) as img:
                # Convert to RGB if needed
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize for web (max 1920px wide)
                max_width = 1920
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Save optimized version
                img.save(web_path, 'JPEG', quality=85, optimize=True)
                
                # Convert to base64 for embedding
                with open(web_path, 'rb') as f:
                    img_base64 = base64.b64encode(f.read()).decode('utf-8')
                    processed_images.append({
                        'index': i,
                        'data_url': f'data:image/jpeg;base64,{img_base64}',
                        'filename': web_name
                    })
                    
        except Exception as e:
            logger.error(f"Error processing image {i}: {e}")
    
    # Calculate timing for smooth transitions
    num_slides = len(processed_images)
    slide_duration = 4  # seconds per slide
    transition_duration = 1  # seconds for fade transition
    total_duration = num_slides * slide_duration
    
    # Generate Ken Burns animations for each slide
    ken_burns_styles = []
    for i in range(num_slides):
        # Alternate between different Ken Burns effects
        if i % 4 == 0:
            # Zoom in from center
            effect = """
                transform: scale(1) translate(0, 0);
                animation: kenburns-1 {duration}s ease-in-out {delay}s infinite;
            """
            keyframes = """
                @keyframes kenburns-1 {
                    0% { transform: scale(1) translate(0, 0); }
                    100% { transform: scale(1.2) translate(0, 0); }
                }
            """
        elif i % 4 == 1:
            # Zoom out from top-left
            effect = """
                transform: scale(1.2) translate(-5%, -5%);
                animation: kenburns-2 {duration}s ease-in-out {delay}s infinite;
            """
            keyframes = """
                @keyframes kenburns-2 {
                    0% { transform: scale(1.2) translate(-5%, -5%); }
                    100% { transform: scale(1) translate(0, 0); }
                }
            """
        elif i % 4 == 2:
            # Pan from left to right
            effect = """
                transform: scale(1.1) translate(-5%, 0);
                animation: kenburns-3 {duration}s ease-in-out {delay}s infinite;
            """
            keyframes = """
                @keyframes kenburns-3 {
                    0% { transform: scale(1.1) translate(-5%, 0); }
                    100% { transform: scale(1.1) translate(5%, 0); }
                }
            """
        else:
            # Pan from right to left with zoom
            effect = """
                transform: scale(1) translate(5%, 0);
                animation: kenburns-4 {duration}s ease-in-out {delay}s infinite;
            """
            keyframes = """
                @keyframes kenburns-4 {
                    0% { transform: scale(1) translate(5%, 0); }
                    50% { transform: scale(1.15) translate(0, 0); }
                    100% { transform: scale(1.1) translate(-5%, 0); }
                }
            """
        
        ken_burns_styles.append({
            'effect': effect.format(duration=slide_duration, delay=i * slide_duration),
            'keyframes': keyframes if i < 4 else ''  # Only define keyframes once
        })
    
    # Generate the HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #000;
            overflow: hidden;
            position: relative;
            height: 100vh;
        }}
        
        .slideshow-container {{
            position: relative;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }}
        
        .slide {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            animation: fade {total_duration}s ease-in-out infinite;
            overflow: hidden;
        }}
        
        .slide img {{
            position: absolute;
            top: 50%;
            left: 50%;
            min-width: 100%;
            min-height: 100%;
            width: auto;
            height: auto;
            transform: translate(-50%, -50%);
            object-fit: cover;
        }}
        
        /* Fade animation for slides */
        @keyframes fade {{
            0% {{ opacity: 0; }}
            {100/num_slides/2}% {{ opacity: 1; }}
            {100/num_slides}% {{ opacity: 1; }}
            {100/num_slides + 100/num_slides/2}% {{ opacity: 0; }}
            100% {{ opacity: 0; }}
        }}
        
        /* Ken Burns effect keyframes */
        @keyframes kenburns-1 {{
            0% {{ transform: scale(1) translate(-50%, -50%); }}
            100% {{ transform: scale(1.2) translate(-50%, -50%); }}
        }}
        
        @keyframes kenburns-2 {{
            0% {{ transform: scale(1.2) translate(-55%, -55%); }}
            100% {{ transform: scale(1) translate(-50%, -50%); }}
        }}
        
        @keyframes kenburns-3 {{
            0% {{ transform: scale(1.1) translate(-55%, -50%); }}
            100% {{ transform: scale(1.1) translate(-45%, -50%); }}
        }}
        
        @keyframes kenburns-4 {{
            0% {{ transform: scale(1) translate(-45%, -50%); }}
            50% {{ transform: scale(1.15) translate(-50%, -50%); }}
            100% {{ transform: scale(1.1) translate(-55%, -50%); }}
        }}
        
        /* Individual slide timings */
        {chr(10).join([f'''
        .slide:nth-child({i+1}) {{
            animation-delay: {i * slide_duration}s;
        }}
        
        .slide:nth-child({i+1}) img {{
            {ken_burns_styles[i]['effect']}
        }}''' for i in range(num_slides)])}
        
        /* Controls */
        .controls {{
            position: absolute;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 10px;
            z-index: 100;
            background: rgba(0, 0, 0, 0.7);
            padding: 15px 25px;
            border-radius: 50px;
            backdrop-filter: blur(10px);
        }}
        
        .control-btn {{
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }}
        
        .control-btn:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }}
        
        /* Property info overlay */
        .property-info {{
            position: absolute;
            top: 30px;
            left: 30px;
            color: white;
            z-index: 100;
            background: rgba(0, 0, 0, 0.7);
            padding: 20px 30px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            max-width: 400px;
        }}
        
        .property-info h1 {{
            font-size: 28px;
            margin-bottom: 10px;
            font-weight: 300;
            letter-spacing: 1px;
        }}
        
        .property-info p {{
            font-size: 16px;
            opacity: 0.9;
            line-height: 1.5;
        }}
        
        /* Progress indicators */
        .progress-dots {{
            position: absolute;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 10px;
            z-index: 100;
        }}
        
        .dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .dot.active {{
            background: white;
            transform: scale(1.2);
        }}
        
        /* Mobile responsive */
        @media (max-width: 768px) {{
            .property-info {{
                top: 20px;
                left: 20px;
                right: 20px;
                padding: 15px 20px;
            }}
            
            .property-info h1 {{
                font-size: 22px;
            }}
            
            .property-info p {{
                font-size: 14px;
            }}
            
            .controls {{
                bottom: 20px;
                padding: 10px 15px;
            }}
            
            .control-btn {{
                padding: 8px 15px;
                font-size: 12px;
            }}
        }}
        
        /* Loading screen */
        .loading {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: #000;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 200;
            transition: opacity 0.5s ease;
        }}
        
        .loading.hidden {{
            opacity: 0;
            pointer-events: none;
        }}
        
        .loading-text {{
            color: white;
            font-size: 20px;
            font-weight: 300;
        }}
    </style>
</head>
<body>
    <div class="loading" id="loading">
        <div class="loading-text">Loading Virtual Tour...</div>
    </div>
    
    <div class="slideshow-container">
        {chr(10).join([f'''
        <div class="slide">
            <img src="{img['data_url']}" alt="Property Image {img['index']+1}" loading="eager">
        </div>''' for img in processed_images])}
    </div>
    
    <div class="property-info">
        <h1>{title}</h1>
        <p>Experience this stunning property through our cinematic virtual tour featuring {num_slides} carefully selected views.</p>
    </div>
    
    <div class="progress-dots">
        {chr(10).join([f'<div class="dot" data-slide="{i}"></div>' for i in range(num_slides)])}
    </div>
    
    <div class="controls">
        <button class="control-btn" onclick="toggleFullscreen()">
            <span>⛶</span> Fullscreen
        </button>
        <button class="control-btn" onclick="toggleMute()">
            <span id="muteIcon">🔇</span> <span id="muteText">Unmute</span>
        </button>
        <a href="#" class="control-btn" onclick="downloadTour()" download>
            <span>⬇</span> Download
        </a>
    </div>
    
    <audio id="bgMusic" loop>
        <source src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3" type="audio/mpeg">
    </audio>
    
    <script>
        // Hide loading screen when ready
        window.addEventListener('load', () => {{
            setTimeout(() => {{
                document.getElementById('loading').classList.add('hidden');
            }}, 1000);
        }});
        
        // Progress dots
        const dots = document.querySelectorAll('.dot');
        const slides = document.querySelectorAll('.slide');
        const slideDuration = {slide_duration * 1000}; // Convert to milliseconds
        let currentSlide = 0;
        
        function updateDots() {{
            dots.forEach((dot, index) => {{
                if (index === currentSlide) {{
                    dot.classList.add('active');
                }} else {{
                    dot.classList.remove('active');
                }}
            }});
        }}
        
        // Update dots based on current slide
        setInterval(() => {{
            currentSlide = (currentSlide + 1) % {num_slides};
            updateDots();
        }}, slideDuration);
        
        // Click dots to jump to slide (simplified for demo)
        dots.forEach((dot, index) => {{
            dot.addEventListener('click', () => {{
                // In a real implementation, you'd pause animations and jump to slide
                alert(`Jump to slide ${{index + 1}} - Feature coming soon!`);
            }});
        }});
        
        // Fullscreen toggle
        function toggleFullscreen() {{
            if (!document.fullscreenElement) {{
                document.documentElement.requestFullscreen();
            }} else {{
                document.exitFullscreen();
            }}
        }}
        
        // Audio controls
        const bgMusic = document.getElementById('bgMusic');
        bgMusic.volume = 0.3; // Set lower volume
        
        function toggleMute() {{
            const muteIcon = document.getElementById('muteIcon');
            const muteText = document.getElementById('muteText');
            
            if (bgMusic.paused) {{
                bgMusic.play();
                muteIcon.textContent = '🔊';
                muteText.textContent = 'Mute';
            }} else {{
                bgMusic.pause();
                muteIcon.textContent = '🔇';
                muteText.textContent = 'Unmute';
            }}
        }}
        
        // Download functionality
        function downloadTour() {{
            const link = document.createElement('a');
            link.href = window.location.href;
            link.download = 'virtual_tour_{job_id}.html';
            link.click();
        }}
        
        // Keyboard controls
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'f' || e.key === 'F') toggleFullscreen();
            if (e.key === 'm' || e.key === 'M') toggleMute();
        }});
    </script>
</body>
</html>"""
    
    # Write the HTML file
    with open(slideshow_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"CSS3 Ken Burns virtual tour created: {slideshow_path}")
    return slideshow_path