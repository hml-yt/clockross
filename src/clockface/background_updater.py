import time
import json
from PIL import Image
from datetime import datetime
import threading
import pygame
import random
import os
from .prompt_generator import PromptGenerator
from ..utils.image_utils import save_debug_image
from ..utils.device_utils import get_best_device
from ..config import Config
from .diffusion_pipeline import DiffusionPipeline

class BackgroundUpdater:
    def __init__(self, debug=False):
        self.config = Config()
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
        
        # Initialize pipeline
        self.pipeline = DiffusionPipeline(debug=debug)
    
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
    
    def _get_background_image(self, hands_surface):
        """Generate a new background image using Stable Diffusion with ControlNet"""
        try:
            # Convert pygame surface (RGB) to PIL Image
            array = pygame.surfarray.array3d(hands_surface)
            # Ensure array is in the correct shape (height, width, channels)
            array = array.transpose(1, 0, 2)
            source_image = Image.fromarray(array)
            
            # Wait for prompt generator to be ready
            while not self.prompt_generator.is_ready():
                time.sleep(0.1)  # Short sleep to prevent CPU spinning
            
            # Generate prompt
            prompt = self.prompt_generator.generate()
            
            if self.debug:
                save_debug_image(source_image, "prerender")
                print(f"\nGenerating image with prompt: {prompt}")
            
            # Generate image using pipeline
            image, seed = self.pipeline.generate(source_image, prompt)
            
            if self.debug:
                save_debug_image(image, "background")
                print("Image generated successfully")
            
            # Store generation metadata
            metadata = {
                "prompt": prompt,
                "seed": seed,
                "checkpoint": os.path.basename(self.config.render['checkpoint']),
                "timestamp": datetime.now().isoformat(),
                "generation_config": self.config.render['generation']
            }
            
            # Update render request in surface manager
            if self.surface_manager:
                self.surface_manager.update_render_request(metadata)
            
            return image
            
        except Exception as e:
            print(f"Error: Failed to generate image: {e}")
            return None
    
    def _do_update(self, hands_surface):
        """Internal method that runs in a separate thread to update the background"""
        try:
            new_bg = self._get_background_image(hands_surface)
            if new_bg:
                with self.lock:
                    # Store the current color as previous for transition
                    self.previous_color = self.current_color
                    self.current_color = self._extract_dominant_color(new_bg)
                    self.transition_start = time.time()
                    
                    # Update background in surface manager
                    if self.surface_manager:
                        self.surface_manager.update_background(new_bg)
                    
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
    
    def update_background(self, hands_surface):
        """Start a background update if conditions are met"""
        current_time = time.time()
        with self.lock:
            # Don't update if we're already updating or if the pipeline is loading
            if self.is_updating or self.pipeline.is_loading or (current_time - self.last_attempt) < self.update_interval:
                return
                
            self.is_updating = True
            self.last_attempt = current_time
            
            # Create and start a new thread for the update
            self.update_thread = threading.Thread(
                target=self._do_update,
                args=(hands_surface,)
            )
            self.update_thread.daemon = True  # Thread will be killed when main program exits
            self.update_thread.start()
    
    def should_update(self):
        """Check if it's time for a background update"""
        return time.time() - self.last_attempt >= self.update_interval
    
    def reload_pipeline(self, complete_callback=None, error_callback=None):
        """Reload the pipeline with new configuration"""
        self.pipeline.reload(complete_callback, error_callback) 
