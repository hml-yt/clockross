import pygame
import argparse
from datetime import datetime
from src.movement import ClockFace
from src.clockface.background_updater import BackgroundUpdater
from src.settings import SettingsUI
from src.clockface.surface_manager import SurfaceManager
from src.config import Config
import os

# Set Hugging Face cache directories
os.environ['HF_HOME'] = os.path.join(os.path.dirname(__file__), 'cache', 'hf')

# Create cache directories if they don't exist
os.makedirs(os.environ['HF_HOME'], exist_ok=True)

# Initialize Pygame
pygame.init()

# Get the display info and load config
display_info = pygame.display.Info()
config = Config()

# Get display settings
FULLSCREEN_WIDTH = display_info.current_w
FULLSCREEN_HEIGHT = display_info.current_h
WINDOWED_WIDTH = config.display['windowed_width']
WINDOWED_HEIGHT = config.display['windowed_height']
RENDER_WIDTH = config.render['width']
RENDER_HEIGHT = config.render['height']
BACKGROUND_COLOR = tuple(config.display['background_color'])

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
        pygame.mouse.set_visible(False)  # Hide cursor only in fullscreen mode
    pygame.display.set_caption("Analog Clock with AI Background")
    
    # Initialize components
    clock = pygame.time.Clock()
    # Use render dimensions for the clock face that will be used for background generation
    render_clock_face = ClockFace(RENDER_WIDTH, RENDER_HEIGHT)
    # Use display dimensions for the actual display clock face
    display_clock_face = ClockFace(display_width, display_height)
    surface_manager = SurfaceManager(display_width, display_height, RENDER_WIDTH, RENDER_HEIGHT, debug=debug)
    background_updater = BackgroundUpdater(debug=debug)
    background_updater.set_surface_manager(surface_manager)
    settings_ui = SettingsUI(display_width, display_height, background_updater, surface_manager)
    
    running = True
    first_background_received = False
    
    # Force initial update
    now = datetime.now()
    hands_surface = render_clock_face.draw_clock_hands(now.hour, now.minute)
    surface_manager.update_hands(hands_surface)
    background_updater.update_background(hands_surface)
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if not settings_ui.handle_click(event.pos):
                        # If settings didn't handle the click, toggle settings
                        settings_ui.toggle()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if settings_ui.visible:
                        settings_ui.visible = False
                    else:
                        running = False
        
        # Get current time
        now = datetime.now()
        hours, minutes, seconds = now.hour, now.minute, now.second
        
        # Draw clock hands (for rendering)
        if background_updater.should_update():
            hands_surface = render_clock_face.draw_clock_hands(hours, minutes)
            surface_manager.update_hands(hands_surface)
            background_updater.update_background(hands_surface)
        
        # Clear screen with pure black
        screen.fill(BACKGROUND_COLOR)
        
        # Draw background with transitions
        bg_surface = surface_manager.get_display_background()
        if bg_surface:
            screen.blit(bg_surface, (0, 0))
        
        # Clear overlay surface
        display_clock_face.overlay_surface.fill((0, 0, 0, 0))
        
        # Draw clock overlay (circle and markers) if configured
        display_clock_face.draw_clock_overlay(display_clock_face.overlay_surface)
        
        # Draw seconds hand on overlay with dominant color
        display_clock_face.draw_seconds_hand(
            display_clock_face.overlay_surface,
            seconds,
            background_updater.get_dominant_color()
        )
        
        # Draw overlay
        screen.blit(display_clock_face.overlay_surface, (0, 0))
        
        # Draw settings UI
        settings_ui.draw(screen)
        
        pygame.display.flip()
        clock.tick(config.display['fps'])

    pygame.quit()

if __name__ == "__main__":
    main() 