import pygame
import argparse
from datetime import datetime
from src.clock import ClockFace
from src.background import BackgroundUpdater
from src.utils import surface_to_base64, save_debug_image

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 640
HEIGHT = 360
API_URL = "http://orinputer.local:7860/sdapi/v1/txt2img"
BACKGROUND_COLOR = (0, 0, 0)  # Pure black

def parse_args():
    parser = argparse.ArgumentParser(description='AI-Powered Analog Clock')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode (save debug images and verbose output)')
    return parser.parse_args()

def main():
    args = parse_args()
    debug = args.debug
    
    # Set up display
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Analog Clock with AI Background")
    
    print("Starting clock application...")
    if debug:
        print("Debug mode enabled - saving debug images and showing verbose output")
    print(f"Will refresh background every 15 seconds")
    print(f"API endpoint: {API_URL}")
    
    # Initialize components
    clock = pygame.time.Clock()
    clock_face = ClockFace(WIDTH, HEIGHT)
    background_updater = BackgroundUpdater(API_URL, debug=debug)
    
    running = True
    first_background_received = False
    
    # Force initial update
    now = datetime.now()
    hands_surface = clock_face.draw_clock_hands(now.hour, now.minute)
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
            hands_surface = clock_face.draw_clock_hands(hours, minutes)
            hands_base64 = surface_to_base64(hands_surface, debug=debug)
            background_updater.update_background(hands_base64)
        
        # Clear screen with pure black
        screen.fill(BACKGROUND_COLOR)
        
        # Draw background if available
        background = background_updater.get_background()
        if background:
            first_background_received = True
            mode = background.mode
            size = background.size
            data = background.tobytes()
            bg_surface = pygame.image.fromstring(data, size, mode)
            screen.blit(bg_surface, (0, 0))
        elif not first_background_received:
            # Show clock hands until first background is received
            screen.blit(hands_surface, (0, 0))
        
        # Clear overlay surface
        clock_face.overlay_surface.fill((0, 0, 0, 0))
        
        # Draw clock face overlay
        clock_face.draw_clock_overlay(clock_face.overlay_surface)
        
        # Draw seconds hand on overlay with dominant color
        clock_face.draw_seconds_hand(
            clock_face.overlay_surface,
            seconds,
            background_updater.get_dominant_color()
        )
        
        # Draw overlay
        screen.blit(clock_face.overlay_surface, (0, 0))
        
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main() 