import pygame
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime
import cv2
import numpy as np
import os
from ..config import Config

def save_debug_image(image, prefix):
    """Save a debug image with timestamp.
    
    Args:
        image: Either a pygame Surface or PIL Image
        prefix: String prefix for the filename (e.g., 'prerender' or 'background')
    """
    timestamp = datetime.now().strftime("%H%M%S")
    os.makedirs("debug", exist_ok=True)
    debug_filename = os.path.join("debug", f"debug_{prefix}_{timestamp}.png")
    
    if isinstance(image, pygame.Surface):
        pygame.image.save(image, debug_filename)
    else:  # PIL Image
        image.save(debug_filename)
    
    print(f"Saved {prefix} debug image to {debug_filename}")

def surface_to_base64(surface, debug=False):
    """Convert a pygame surface to base64 string.
    The surface should be in RGBA format with a black background and white clock hands."""
    # First ensure we're working with RGBA
    if surface.get_bitsize() != 32:
        temp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        temp.blit(surface, (0, 0))
        surface = temp

    # Convert to PIL Image
    string_image = pygame.image.tostring(surface, 'RGBA')
    pil_image = Image.frombytes('RGBA', surface.get_size(), string_image)
    
    # Convert to RGB with white on black background
    # This ensures the renderer gets a clean black and white image
    rgb_image = Image.new('RGB', pil_image.size, (0, 0, 0))
    rgb_image.paste(pil_image, mask=pil_image.split()[3])  # Use alpha as mask
    
    # Save debug image if requested
    if debug:
        save_debug_image(rgb_image, "prerender")
    
    # Convert to base64
    buffered = BytesIO()
    rgb_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
        
    return img_str

def scale_pil_image_to_display(pil_image, target_width, target_height):
    """Scale a PIL image to the target resolution"""
    # Convert PIL to CV2
    cv2_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    # Calculate scaling factors
    scale_x = target_width / cv2_image.shape[1]
    scale_y = target_height / cv2_image.shape[0]
    
    # Use area interpolation for downscaling, Lanczos for upscaling
    if scale_x < 1 or scale_y < 1:
        interpolation = cv2.INTER_AREA
    else:
        interpolation = cv2.INTER_LANCZOS4
    
    # Scale image
    scaled = cv2.resize(cv2_image, (target_width, target_height), 
                       interpolation=interpolation)
    
    # Convert back to PIL
    return Image.fromarray(cv2.cvtColor(scaled, cv2.COLOR_BGR2RGB))

def pil_to_cv2(pil_image):
    """Convert PIL image to CV2 format"""
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

def cv2_to_surface(cv2_image):
    """Convert CV2 image to pygame surface"""
    rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    return pygame.surfarray.make_surface(rgb_image.swapaxes(0, 1))

def get_dominant_color(surface):
    """Extract the brightest color from a pygame surface.
    
    Args:
        surface: Pygame surface to analyze
        
    Returns:
        Tuple of (R,G,B) representing the brightest color
    """
    # Convert surface to array
    arr = pygame.surfarray.array3d(surface)
    # Resize to speed up processing
    arr = arr[::4, ::4]
    # Find brightest pixel
    brightest_idx = np.argmax(np.sum(arr, axis=2))
    brightest_pixel = arr.reshape(-1, 3)[brightest_idx]
    return tuple(brightest_pixel)

def morph_transition(prev_frame, next_frame, progress):
    """Create a morphed transition between two frames using optical flow.
    
    Args:
        prev_frame: Previous frame (CV2 format)
        next_frame: Next frame (CV2 format)
        progress: Transition progress from 0 to 1
        
    Returns:
        Morphed frame
    """
    config = Config()
    flow_params = config.animation['morph_flow_params']
    
    # Convert frames to grayscale for optical flow
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    next_gray = cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY)
    
    # Calculate optical flow
    flow = cv2.calcOpticalFlowFarneback(
        prev_gray, 
        next_gray,
        None,
        flow_params['pyr_scale'],
        flow_params['levels'],
        flow_params['winsize'],
        flow_params['iterations'],
        flow_params['poly_n'],
        flow_params['poly_sigma'],
        flow_params['flags']
    )
    
    # Create meshgrid for warping
    h, w = prev_frame.shape[:2]
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    
    # Scale flow by progress
    flow *= progress
    
    # Calculate destination points
    dst_x = x + flow[..., 0]
    dst_y = y + flow[..., 1]
    
    # Warp previous frame towards next frame
    warped = cv2.remap(prev_frame, dst_x, dst_y, cv2.INTER_LINEAR)
    
    # Blend warped frame with next frame based on progress
    return cv2.addWeighted(warped, 1 - progress, next_frame, progress, 0) 