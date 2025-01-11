import pygame
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime

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