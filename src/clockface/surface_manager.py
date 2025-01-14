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
    morph_transition
)

class SurfaceManager:
    def __init__(self, display_width, display_height, api_width, api_height, debug=False):
        self.display_width = display_width
        self.display_height = display_height
        self.api_width = api_width
        self.api_height = api_height
        self.debug = debug
        
        # Clock surfaces
        self.hands_surface = None
        self.hands_base64 = None
        
        # Background surfaces
        self.current_background = None
        self.previous_background = None
        self.transition_start = 0
        self.transition_duration = 1.0  # Will be updated from config
        
        # API state
        self.last_api_request = None
        
        # Create snapshots directory
        self.snapshots_dir = "snapshots"
        os.makedirs(self.snapshots_dir, exist_ok=True)
    
    def update_hands(self, hands_surface):
        """Update the clock hands surface and its base64 representation"""
        self.hands_surface = hands_surface
        self.hands_base64 = surface_to_base64(hands_surface, self.debug)
        return self.hands_base64
    
    def update_background(self, new_background, transition_duration):
        """Update the background with transition state"""
        self.transition_duration = transition_duration
        if self.current_background:
            self.previous_background = self.current_background
        self.current_background = new_background
        self.transition_start = time.time()
    
    def get_background_state(self):
        """Get current background state including transition progress"""
        if not self.current_background:
            return None, None, 1.0
            
        progress = min(1.0, (time.time() - self.transition_start) / self.transition_duration)
        return self.current_background, self.previous_background, progress
    
    def get_display_background(self):
        """Get the background scaled and processed for display"""
        background_info = self.get_background_state()
        if not background_info[0]:  # If no current background
            if not self.hands_surface:
                return None
            # Show clock hands until first background is received
            return pygame.transform.smoothscale(self.hands_surface, (self.display_width, self.display_height))
        
        current_bg, prev_bg, progress = background_info
        
        # Scale current background
        scaled_current = scale_pil_image_to_display(current_bg, self.display_width, self.display_height)
        
        if prev_bg and progress < 1.0:
            # Scale previous background
            scaled_prev = scale_pil_image_to_display(prev_bg, self.display_width, self.display_height)
            
            # Convert to CV2 format for morphing
            cv2_current = pil_to_cv2(scaled_current)
            cv2_prev = pil_to_cv2(scaled_prev)
            
            # Create morphed transition
            morphed = morph_transition(cv2_prev, cv2_current, progress)
            
            # Convert back to pygame surface
            return cv2_to_surface(morphed)
        else:
            # Just return current background
            return pygame.image.fromstring(
                scaled_current.tobytes(),
                scaled_current.size,
                scaled_current.mode
            )
    
    def update_api_request(self, api_request):
        """Update the last API request"""
        self.last_api_request = api_request
    
    def save_snapshot(self):
        """Save all current surfaces and state to snapshot files"""
        if not self.hands_surface:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save clock face
        pygame.image.save(self.hands_surface, f"{self.snapshots_dir}/{timestamp}_1_clock.png")
        
        # Save API request if available
        if self.last_api_request:
            with open(f"{self.snapshots_dir}/{timestamp}_2_api_request.json", 'w') as f:
                json.dump(self.last_api_request, f, indent=2)
        
        # Save current background if available
        if self.current_background:
            self.current_background.save(f"{self.snapshots_dir}/{timestamp}_3_background.png") 