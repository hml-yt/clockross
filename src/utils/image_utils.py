import pygame
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime
import cv2
import numpy as np
from ..config import Config

def enhance_image(cv2_image):
    """Apply image enhancement techniques"""
    config = Config()
    
    # Apply bilateral filter for noise reduction while preserving edges
    bf = config.enhancement['bilateral_filter']
    denoised = cv2.bilateralFilter(cv2_image, bf['d'], bf['sigma_color'], bf['sigma_space'])
    
    # Enhance details using unsharp masking
    um = config.enhancement['unsharp_mask']
    gaussian = cv2.GaussianBlur(denoised, tuple(um['blur_size']), um['sigma'])
    unsharp_image = cv2.addWeighted(denoised, 1 + um['amount'], gaussian, um['threshold'], 0)
    
    # Enhance contrast using CLAHE
    clahe_config = config.enhancement['clahe']
    lab = cv2.cvtColor(unsharp_image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(
        clipLimit=clahe_config['clip_limit'],
        tileGridSize=tuple(clahe_config['tile_grid_size'])
    )
    cl = clahe.apply(l)
    enhanced = cv2.merge((cl,a,b))
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    return enhanced

def scale_pil_image_to_display(pil_image, target_width, target_height):
    """Scale a PIL image to the target resolution with enhanced quality"""
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
    config = Config()
    flow_params = config.animation['morph_flow_params']
    
    # Convert to grayscale for optical flow
    old_gray = cv2.cvtColor(old_img, cv2.COLOR_BGR2GRAY)
    new_gray = cv2.cvtColor(new_img, cv2.COLOR_BGR2GRAY)
    
    # Calculate optical flow with configurable parameters
    flow = cv2.calcOpticalFlowFarneback(
        old_gray, new_gray,
        None,
        flow_params['pyr_scale'],
        flow_params['levels'],
        flow_params['winsize'],
        flow_params['iterations'],
        flow_params['poly_n'],
        flow_params['poly_sigma'],
        flow_params['flags']
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
    # This ensures the API gets a clean black and white image
    rgb_image = Image.new('RGB', pil_image.size, (0, 0, 0))
    rgb_image.paste(pil_image, mask=pil_image.split()[3])  # Use alpha as mask
    
    # Save the pre-API image for debugging
    if debug:
        timestamp = datetime.now().strftime("%H%M%S")
        debug_filename = f"debug_preapi_{timestamp}.png"
        rgb_image.save(debug_filename)
        print(f"Saved pre-API image to {debug_filename}")
    
    # Convert to base64
    buffered = BytesIO()
    rgb_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
        
    return img_str

def save_debug_image(image, prefix):
    """Save a debug image with timestamp.
    
    Args:
        image: Either a pygame Surface or PIL Image
        prefix: String prefix for the filename (e.g., 'clockface' or 'background')
    """
    timestamp = datetime.now().strftime("%H%M%S")
    debug_filename = f"debug_{prefix}_{timestamp}.png"
    
    if isinstance(image, pygame.Surface):
        pygame.image.save(image, debug_filename)
    else:  # PIL Image
        image.save(debug_filename)
    
    print(f"Saved {prefix} to {debug_filename}") 