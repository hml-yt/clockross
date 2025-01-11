import time
import json
import base64
import requests
import threading
from io import BytesIO
from PIL import Image
from datetime import datetime
from .prompt_generator import PromptGenerator
from ..utils import save_debug_image

class BackgroundUpdater:
    def __init__(self, api_url, debug=False):
        self.api_url = api_url
        self.debug = debug
        self.background = None
        self.lock = threading.Lock()
        self.last_attempt = 0
        self.is_updating = False
        self.update_thread = None
        self.dominant_color = (255, 255, 255, 75)  # Default color
        self.prompt_generator = PromptGenerator()
    
    def _extract_dominant_color(self, pil_image):
        """Extract the brightest color from the image (likely the clock hands/markers)"""
        # Convert to RGB if not already
        rgb_image = pil_image.convert('RGB')
        # Resize to speed up processing
        rgb_image.thumbnail((100, 100))
        
        # Get pixel data
        pixels = list(rgb_image.getdata())
        
        # Calculate brightness for each pixel and find the brightest one
        brightest_pixel = max(pixels, key=lambda p: sum(p))
        
        # Make it very transparent (75 for ~15% opacity)
        return (*brightest_pixel, 75)
    
    def _get_background_image(self, clock_image_base64):
        """Get a new background image from the Stable Diffusion API"""
        with open('api_payload.json', 'r') as f:
            payload = json.load(f)
        
        payload["prompt"] = self.prompt_generator.generate()
        payload["alwayson_scripts"]["controlnet"]["args"][0]["image"] = clock_image_base64
        
        if self.debug:
            print("\nSending request to Stable Diffusion API...")
        try:
            response = requests.post(self.api_url, json=payload, timeout=30)
            if response.status_code == 200:
                if self.debug:
                    print("Received response from API")
                image_data = base64.b64decode(response.json()['images'][0])
                image = Image.open(BytesIO(image_data))
                if self.debug:
                    save_debug_image(image, "background")
                return image
            print(f"Error: API request failed with status code {response.status_code}")
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"Error: Could not connect to API server: {e}")
        except Exception as e:
            print(f"Error: Unexpected error during API request: {e}")
        return None
    
    def _do_update(self, clock_image_base64):
        """Internal method that runs in a separate thread to update the background"""
        try:
            new_bg = self._get_background_image(clock_image_base64)
            if new_bg:
                with self.lock:
                    self.background = new_bg
                    self.dominant_color = self._extract_dominant_color(new_bg)
                    if self.debug:
                        print(f"Background updated at {datetime.now().strftime('%H:%M:%S')}")
                        print(f"New brightest color: RGB{self.dominant_color[:3]} (15% opacity)")
        finally:
            with self.lock:
                self.is_updating = False
                self.update_thread = None
    
    def get_background(self):
        """Get the current background image"""
        with self.lock:
            return self.background
    
    def get_dominant_color(self):
        """Get the current dominant color"""
        with self.lock:
            return self.dominant_color
    
    def update_background(self, clock_image_base64):
        """Start a background update if conditions are met"""
        current_time = time.time()
        with self.lock:
            if self.is_updating or (current_time - self.last_attempt) < 15:
                return
            self.is_updating = True
            self.last_attempt = current_time
            
            # Create and start a new thread for the update
            self.update_thread = threading.Thread(
                target=self._do_update,
                args=(clock_image_base64,)
            )
            self.update_thread.daemon = True  # Thread will be killed when main program exits
            self.update_thread.start()
    
    def should_update(self):
        """Check if it's time for a background update"""
        return time.time() - self.last_attempt >= 15 