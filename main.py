import pygame
import argparse
from datetime import datetime
from src.clock import ClockFace
from src.background import BackgroundUpdater
from src.utils import surface_to_base64, save_debug_image
from PIL import Image
import numpy as np
import cv2

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

def enhance_image(cv2_image):
    """Apply image enhancement techniques"""
    # Apply bilateral filter for noise reduction while preserving edges
    denoised = cv2.bilateralFilter(cv2_image, 9, 75, 75)
    
    # Enhance details using unsharp masking
    gaussian = cv2.GaussianBlur(denoised, (0, 0), 3.0)
    unsharp_image = cv2.addWeighted(denoised, 1.5, gaussian, -0.5, 0)
    
    # Enhance contrast using CLAHE
    lab = cv2.cvtColor(unsharp_image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    enhanced = cv2.merge((cl,a,b))
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    return enhanced

def scale_pil_image_to_display(pil_image):
    """Scale a PIL image to the display resolution with enhanced quality"""
    # Convert PIL to CV2
    cv2_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    # Calculate scaling factors
    scale_x = DISPLAY_WIDTH / cv2_image.shape[1]
    scale_y = DISPLAY_HEIGHT / cv2_image.shape[0]
    
    # Use area interpolation for downscaling, Lanczos for upscaling
    if scale_x < 1 or scale_y < 1:
        interpolation = cv2.INTER_AREA
    else:
        interpolation = cv2.INTER_LANCZOS4
    
    # Scale image
    scaled = cv2.resize(cv2_image, (DISPLAY_WIDTH, DISPLAY_HEIGHT), 
                       interpolation=interpolation)
    
    # Apply enhancement
    enhanced = enhance_image(scaled)
    
    # Convert back to PIL
    return Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB))

def pil_to_cv2(pil_image):
    """Convert PIL image to CV2 format"""
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

def cv2_to_surface(cv2_image):
    """Convert CV2 image to pygame surface"""
    rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    return pygame.surfarray.make_surface(rgb_image.swapaxes(0, 1))

def morph_transition(old_img, new_img, progress):
    """Create a morphing effect between images using optical flow"""
    # Convert to grayscale for optical flow
    old_gray = cv2.cvtColor(old_img, cv2.COLOR_BGR2GRAY)
    new_gray = cv2.cvtColor(new_img, cv2.COLOR_BGR2GRAY)
    
    # Calculate optical flow
    flow = cv2.calcOpticalFlowFarneback(
        old_gray, new_gray,
        None, 0.5, 3, 15, 3, 5, 1.2, 0
    )
    
    # Create the morphed image
    h, w = old_img.shape[:2]
    flow_map = np.float32(np.mgrid[:h, :w].transpose(1, 2, 0))
    flow_map += flow * progress
    
    # Warp the old image
    morphed = cv2.remap(
        old_img,
        flow_map[:, :, 1],
        flow_map[:, :, 0],
        cv2.INTER_LINEAR
    )
    
    # Blend between morphed and new image
    return cv2.addWeighted(morphed, 1-progress, new_img, progress, 0)

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
        
        # Get background and transition state
        background_info = background_updater.get_background()
        if background_info[0]:  # If we have a current background
            first_background_received = True
            current_bg, prev_bg, progress = background_info
            
            # Scale current background
            scaled_current = scale_pil_image_to_display(current_bg)
            
            if prev_bg and progress < 1.0:
                # Scale previous background
                scaled_prev = scale_pil_image_to_display(prev_bg)
                
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