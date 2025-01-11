import pygame
import argparse
from datetime import datetime
from src.clock import ClockFace
from src.background import BackgroundUpdater
from src.utils import surface_to_base64, save_debug_image
from PIL import Image

# Initialize Pygame
pygame.init()

# Constants
DISPLAY_WIDTH = 1024
DISPLAY_HEIGHT = 600
API_WIDTH = 640
API_HEIGHT = 360
API_URL = "http://orinputer.local:7860/sdapi/v1/txt2img"
BACKGROUND_COLOR = (0, 0, 0)  # Pure black

def parse_args():
    parser = argparse.ArgumentParser(description='AI-Powered Analog Clock')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode (save debug images and verbose output)')
    return parser.parse_args()

def scale_pil_image_to_display(pil_image):
    """Scale a PIL image to the display resolution"""
    return pil_image.resize((DISPLAY_WIDTH, DISPLAY_HEIGHT), Image.Resampling.LANCZOS)

def main():
    args = parse_args()
    debug = args.debug
    
    # Set up display
    screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
    pygame.display.set_caption("Analog Clock with AI Background")
    
    print("Starting clock application...")
    if debug:
        print("Debug mode enabled - saving debug images and showing verbose output")
    print(f"Will refresh background every 15 seconds")
    print(f"API endpoint: {API_URL}")
    
    # Initialize components
    clock = pygame.time.Clock()
    # Use API dimensions for the clock face that will be sent to the API
    api_clock_face = ClockFace(API_WIDTH, API_HEIGHT)
    # Use display dimensions for the actual display clock face
    display_clock_face = ClockFace(DISPLAY_WIDTH, DISPLAY_HEIGHT)
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
        
        # Draw background if available
        background = background_updater.get_background()
        if background:
            first_background_received = True
            # Scale the background to display resolution
            scaled_bg = scale_pil_image_to_display(background)
            mode = scaled_bg.mode
            size = scaled_bg.size
            data = scaled_bg.tobytes()
            bg_surface = pygame.image.fromstring(data, size, mode)
            screen.blit(bg_surface, (0, 0))
        else:
            # Only draw clock overlay when there's no background
            # Clear overlay surface
            display_clock_face.overlay_surface.fill((0, 0, 0, 0))
            
            # Draw clock face overlay at display resolution
            display_clock_face.draw_clock_overlay(display_clock_face.overlay_surface)
            
            if not first_background_received:
                # Show clock hands until first background is received
                # Scale the hands surface to display resolution
                scaled_hands = pygame.transform.smoothscale(hands_surface, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
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