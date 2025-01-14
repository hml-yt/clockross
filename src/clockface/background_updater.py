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
from ..config import Config

class BackgroundUpdater:
    def __init__(self, api_url, debug=False):
        self.config = Config()
        self.api_url = api_url
        self.debug = debug
        self.surface_manager = None
        self.current_color = (255, 255, 255, self.config.clock['overlay_opacity'])  # Default color
        self.previous_color = None
        self.transition_start = 0
        self.transition_duration = self.config.animation['transition_duration']
        self.update_interval = self.config.animation['background_update_interval']
        self.lock = threading.Lock()
        self.last_attempt = 0
        self.is_updating = False
        self.update_thread = None
        self.prompt_generator = PromptGenerator()
    
    def set_surface_manager(self, surface_manager):
        """Set the surface manager instance"""
        self.surface_manager = surface_manager
    
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
        
        # Make it transparent according to config
        return (*brightest_pixel, self.config.clock['overlay_opacity'])
    
    def _get_background_image(self, clock_image_base64):
        """Get a new background image from the Stable Diffusion API"""
        with open('api_payload.json', 'r') as f:
            payload = json.load(f)
        
        # Override dynamic values
        payload["prompt"] = self.prompt_generator.generate()
        payload["alwayson_scripts"]["controlnet"]["args"][0]["image"] = clock_image_base64
        
        # Override checkpoint only if not using default
        if self.config.api['checkpoint'] != 'default':
            payload["override_settings"]["sd_model_checkpoint"] = self.config.api['checkpoint']
        elif "override_settings" in payload:
            # Remove override_settings if using default and it exists
            if "sd_model_checkpoint" in payload["override_settings"]:
                del payload["override_settings"]["sd_model_checkpoint"]
            # Remove entire override_settings if empty
            if not payload["override_settings"]:
                del payload["override_settings"]
        
        if self.debug:
            print("\nSending request to Stable Diffusion API...")
            if self.config.api['checkpoint'] != 'default':
                print(f"Using checkpoint: {self.config.api['checkpoint']}")
            else:
                print("Using default checkpoint")
        try:
            response = requests.post(self.api_url, json=payload, timeout=30)
            if response.status_code == 200:
                if self.debug:
                    print("Received response from API")
                image_data = base64.b64decode(response.json()['images'][0])
                image = Image.open(BytesIO(image_data))
                if self.debug:
                    save_debug_image(image, "background")
                    
                # Update API request in surface manager
                if self.surface_manager:
                    self.surface_manager.update_api_request(payload)
                    
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
                    # Store the current color as previous for transition
                    self.previous_color = self.current_color
                    self.current_color = self._extract_dominant_color(new_bg)
                    
                    # Update background in surface manager
                    if self.surface_manager:
                        self.surface_manager.update_background(new_bg, self.transition_duration)
                    
                    if self.debug:
                        print(f"Background updated at {datetime.now().strftime('%H:%M:%S')}")
                        print(f"New brightest color: RGB{self.current_color[:3]} (15% opacity)")
        finally:
            with self.lock:
                self.is_updating = False
                self.update_thread = None
    
    def _interpolate_color(self, color1, color2, progress):
        """Interpolate between two colors"""
        if not color1 or not color2:
            return color2 or color1
        return tuple(
            int(c1 + (c2 - c1) * progress)
            for c1, c2 in zip(color1, color2)
        )
    
    def get_dominant_color(self):
        """Get the current dominant color with transition"""
        with self.lock:
            if not self.previous_color:
                return self.current_color
            
            # Calculate transition progress
            progress = min(1.0, (time.time() - self.transition_start) / self.transition_duration)
            
            # Interpolate between previous and current color
            return self._interpolate_color(self.previous_color, self.current_color, progress)
    
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
        return time.time() - self.last_attempt >= self.update_interval 