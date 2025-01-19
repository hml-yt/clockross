import pygame
import base64
import cv2
import numpy as np
import json
import os
import time
from PIL import Image
from io import BytesIO
from datetime import datetime
from ..utils.image_utils import (
    surface_to_base64,
    scale_pil_image_to_display,
    pil_to_cv2,
    cv2_to_surface,
    morph_transition,
    save_debug_image
)
from ..config import Config

class SurfaceManager:
    """Manages the various surfaces used in the clock display"""
    
    def __init__(self, display_width, display_height, render_width, render_height, debug=False):
        """Initialize the surface manager"""
        self.config = Config()
        self.display_width = display_width
        self.display_height = display_height
        self.render_width = render_width
        self.render_height = render_height
        self.debug = debug
        
        # Initialize surfaces
        self.hands_surface = None
        self.background_surface = None
        self.prev_background = None
        self.transition_progress = 0.0
        
        # Render state
        self.last_render_request = None
        
        # Create snapshots directory
        self.snapshots_dir = "snapshots"
        os.makedirs(self.snapshots_dir, exist_ok=True)
    
    def update_hands(self, surface):
        """Update the hands surface and return base64 encoded PNG"""
        self.hands_surface = surface
        return surface_to_base64(surface, self.debug)
    
    def update_background(self, image_data):
        """Update the background surface with new image data"""
        # Save previous background for transitions
        if self.background_surface:
            self.prev_background = self.background_surface
            self.transition_progress = 0.0
        
        # Convert PIL Image to pygame surface
        mode = image_data.mode
        size = image_data.size
        data = image_data.tobytes()
        self.background_surface = pygame.image.fromstring(data, size, mode)
        
        if self.debug:
            save_debug_image(pygame.surfarray.array3d(self.background_surface), "background")
    
    def get_display_background(self):
        """Get the current background surface, handling transitions"""
        if not self.background_surface:
            if not self.hands_surface:
                return None
            # Show clock hands until first background is received
            return pygame.transform.scale(self.hands_surface, (self.display_width, self.display_height))
            
        # Handle transitions
        if self.prev_background and self.transition_progress < 1.0:
            # Update transition progress based on config duration
            fps = self.config.display['fps']
            duration = self.config.animation['transition_duration']
            self.transition_progress += 1.0 / (fps * duration)
            self.transition_progress = min(1.0, self.transition_progress)
            
            # Create transition surface
            transition = pygame.Surface((self.display_width, self.display_height))
            
            # Draw previous and current backgrounds
            transition.blit(pygame.transform.scale(self.prev_background, (self.display_width, self.display_height)), (0, 0))
            current = pygame.transform.scale(self.background_surface, (self.display_width, self.display_height))
            
            # Set alpha for current background
            current.set_alpha(int(255 * self.transition_progress))
            
            # Blend backgrounds
            transition.blit(current, (0, 0))
            return transition
        else:
            # Return scaled background
            return pygame.transform.scale(self.background_surface, (self.display_width, self.display_height))
    
    def update_render_request(self, render_request):
        """Update the last render request"""
        self.last_render_request = render_request
    
    def save_metadata(self, index):
        """Save metadata about the current state"""
        metadata = {
            "index": index,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save render request if available
        if self.last_render_request:
            metadata.update({
                "prompt": self.last_render_request["prompt"],
                "seed": self.last_render_request["seed"],
                "checkpoint": self.last_render_request["checkpoint"],
                "timestamp": self.last_render_request["timestamp"],
                "generation_config": {
                    "controlnet_conditioning_scale": self.last_render_request["generation_config"]["controlnet_conditioning_scale"],
                    "num_inference_steps": self.last_render_request["generation_config"]["num_inference_steps"],
                    "guidance_scale": self.last_render_request["generation_config"]["guidance_scale"],
                    "control_guidance_start": self.last_render_request["generation_config"]["control_guidance_start"],
                    "control_guidance_end": self.last_render_request["generation_config"]["control_guidance_end"]
                }
            })
        
        return metadata
    
    def save_snapshot(self):
        """Save all current surfaces and state to snapshot files"""
        if not self.hands_surface:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save clock face
        pygame.image.save(self.hands_surface, f"{self.snapshots_dir}/{timestamp}_1_clock.png")
        
        # Save metadata
        metadata = self.save_metadata(0)
        with open(f"{self.snapshots_dir}/{timestamp}_2_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        if self.debug:
            print(f"Saved metadata with seed {metadata['seed']} and checkpoint {metadata['checkpoint']}")
        
        # Save current background if available
        if self.background_surface:
            pygame.image.save(self.background_surface, f"{self.snapshots_dir}/{timestamp}_3_background.png") 