import pygame
import argparse
from datetime import datetime
from src.clock import ClockFace
from src.background import BackgroundUpdater
from src.utils import (
    surface_to_base64,
    save_debug_image,
    scale_pil_image_to_display,
    pil_to_cv2,
    cv2_to_surface,
    morph_transition
)
from PIL import Image
import numpy as np
import cv2

# Initialize Pygame
pygame.init()

# Get the display info
display_info = pygame.display.Info()
FULLSCREEN_WIDTH = display_info.current_w
FULLSCREEN_HEIGHT = display_info.current_h
WINDOWED_WIDTH = 1024
WINDOWED_HEIGHT = 600
API_WIDTH = 640
API_HEIGHT = 360
API_URL = "http://orinputer.local:7860/sdapi/v1/txt2img"
BACKGROUND_COLOR = (0, 0, 0)  # Pure black

def parse_args():
    parser = argparse.ArgumentParser(description='AI-Powered Analog Clock')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode (save debug images and verbose output)')
    parser.add_argument('--windowed', action='store_true', help='Run in windowed mode instead of fullscreen')
    return parser.parse_args()

def main():
    args = parse_args()
    debug = args.debug
    
    # Set up display
    if args.windowed:
        screen = pygame.display.set_mode((WINDOWED_WIDTH, WINDOWED_HEIGHT))
        display_width, display_height = WINDOWED_WIDTH, WINDOWED_HEIGHT
    else:
        screen = pygame.display.set_mode((FULLSCREEN_WIDTH, FULLSCREEN_HEIGHT), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        display_width, display_height = FULLSCREEN_WIDTH, FULLSCREEN_HEIGHT
    pygame.display.set_caption("Analog Clock with AI Background")
    
    # Hide the cursor in fullscreen mode
    if not args.windowed:
        pygame.mouse.set_visible(False)
    
    print("Starting clock application...")
    if debug:
        print("Debug mode enabled - saving debug images and showing verbose output")
    print(f"Display resolution: {display_width}x{display_height}")
    print(f"Will refresh background every 15 seconds")
    print(f"API endpoint: {API_URL}")
    
    # Initialize components
    clock = pygame.time.Clock()
    # Use API dimensions for the clock face that will be sent to the API
    api_clock_face = ClockFace(API_WIDTH, API_HEIGHT)
    # Use display dimensions for the actual display clock face
    display_clock_face = ClockFace(display_width, display_height)
    background_updater = BackgroundUpdater(API_URL, debug=debug)
    
    running = True
    first_background_received = False
    
    # Force initial update
    now = datetime.now()
    hands_surface = api_clock_face.draw_clock_hands(now.hour, now.minute)
    hands_base64 = surface_to_base64(hands_surface, debug=debug)
    background_updater.update_background(hands_base64)
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Get current time
        now = datetime.now()
        hours, minutes, seconds = now.hour, now.minute, now.second
        
        # Draw clock hands (for API only)
        if background_updater.should_update():
            hands_surface = api_clock_face.draw_clock_hands(hours, minutes)
            hands_base64 = surface_to_base64(hands_surface, debug=debug)
            background_updater.update_background(hands_base64)
        
        # Clear screen with pure black
        screen.fill(BACKGROUND_COLOR)
        
        # Get background and transition state
        background_info = background_updater.get_background()
        if background_info[0]:  # If we have a current background
            first_background_received = True
            current_bg, prev_bg, progress = background_info
            
            # Scale current background
            scaled_current = scale_pil_image_to_display(current_bg, display_width, display_height)
            
            if prev_bg and progress < 1.0:
                # Scale previous background
                scaled_prev = scale_pil_image_to_display(prev_bg, display_width, display_height)
                
                # Convert to CV2 format for morphing
                cv2_current = pil_to_cv2(scaled_current)
                cv2_prev = pil_to_cv2(scaled_prev)
                
                # Create morphed transition
                morphed = morph_transition(cv2_prev, cv2_current, progress)
                
                # Convert back to pygame surface
                bg_surface = cv2_to_surface(morphed)
                screen.blit(bg_surface, (0, 0))
            else:
                # Just draw current background
                current_surface = pygame.image.fromstring(
                    scaled_current.tobytes(),
                    scaled_current.size,
                    scaled_current.mode
                )
                screen.blit(current_surface, (0, 0))
        else:
            # Only draw clock overlay when there's no background
            # Clear overlay surface
            display_clock_face.overlay_surface.fill((0, 0, 0, 0))
            
            # Draw clock face overlay at display resolution
            display_clock_face.draw_clock_overlay(display_clock_face.overlay_surface)
            
            if not first_background_received:
                # Show clock hands until first background is received
                # Scale the hands surface to display resolution
                scaled_hands = pygame.transform.smoothscale(hands_surface, (display_width, display_height))
                screen.blit(scaled_hands, (0, 0))
        
        # Always draw the seconds hand
        # Clear seconds hand surface
        display_clock_face.overlay_surface.fill((0, 0, 0, 0))
        
        # Draw seconds hand on overlay with dominant color
        display_clock_face.draw_seconds_hand(
            display_clock_face.overlay_surface,
            seconds,
            background_updater.get_dominant_color()
        )
        
        # Draw overlay
        screen.blit(display_clock_face.overlay_surface, (0, 0))
        
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main() 