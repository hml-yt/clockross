import pygame
import math
import time
import json
import base64
import requests
import threading
import random
from io import BytesIO
from PIL import Image
import numpy as np
from datetime import datetime

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 640
HEIGHT = 360
CENTER = (WIDTH // 2, HEIGHT // 2)
CLOCK_RADIUS = min(WIDTH, HEIGHT) // 2 - 20  # Enlarged to almost fill the window
MARKER_LENGTH = 30  # Length of hour markers
HOUR_HAND_LENGTH = CLOCK_RADIUS * 0.6  # Longer hour hand
MINUTE_HAND_LENGTH = CLOCK_RADIUS * 0.8  # Longer minute hand
SECOND_HAND_LENGTH = CLOCK_RADIUS * 0.9  # Longer second hand
API_URL = "http://orinputer.local:7860/sdapi/v1/txt2img"
BACKGROUND_COLOR = (0, 0, 0)  # Pure black

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (25, 25, 25)  # Dark gray for API background
TRANSPARENT_WHITE = (255, 255, 255, 75)  # Semi-transparent white

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Analog Clock with AI Background")

# Create surfaces for drawing
api_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)  # For sending to API
overlay_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)  # For clock overlay

def generate_random_prompt():
    # Time and lighting
    times = [
        "at dawn", "at dusk", "under moonlight", "in twilight", "at midnight",
        "during golden hour", "under a blood moon", "during solar eclipse",
        "in perpetual twilight", "under starlight", "at sunrise", "at sunset"
    ]
    
    # Environments and landscapes
    environments = [
        "in a crystalline cave", "in an ancient temple", "in a floating city",
        "in a submerged cathedral", "in a cosmic void", "in a quantum realm",
        "in a steampunk workshop", "in a celestial observatory",
        "in a forgotten library", "in an enchanted forest", "in a desert oasis",
        "in a volcanic sanctuary", "in an arctic cathedral", "in a cloud kingdom",
        "in a bioluminescent grove", "in a crystal canyon", "in a meteor crater",
        "in a temporal nexus", "in an astral plane", "in a dimensional rift"
    ]
    
    # Main subjects and focal points
    main_elements = [
        "a grand clockwork mechanism", "an ancient timekeeper's sanctuary",
        "a cosmic observatory", "a temporal dimension", "a time-bending realm",
        "a celestial chronometer", "an ethereal timescape", "a time wizard's study",
        "a chronograph temple", "a temporal engine", "a reality-warping device",
        "an interdimensional timepiece", "a cosmic time portal", "a quantum clock tower",
        "an astrolabe sanctuary", "a temporal compass", "a time crystal formation",
        "a mechanical constellation", "a dimensional sundial", "an ethereal hourglass"
    ]
    
    # Atmospheric elements and details
    details = [
        "intricate gears floating in space", "swirling time spirals",
        "floating numerical constellations", "temporal energy streams",
        "crystalline chronographs", "orbiting time fragments",
        "cascading light particles", "flowing time rivers", "dancing auroras",
        "geometric light patterns", "holographic time glyphs", "levitating crystals",
        "temporal storm clouds", "quantum dust motes", "prismatic refractions",
        "nebulous time streams", "fractal patterns", "cosmic clockwork",
        "temporal butterflies", "chronometric fractals", "time-worn artifacts",
        "ethereal wisps", "dimensional echoes", "crystalline formations",
        "ancient runes", "floating mathematical equations", "astral projections"
    ]
    
    # Mood and atmosphere
    atmospheres = [
        "serene and mysterious", "enigmatic and profound",
        "timeless and ethereal", "cosmic and surreal",
        "mystical and ancient", "otherworldly and transcendent",
        "dreamlike and floating", "metaphysical and abstract",
        "sacred and divine", "infinite and vast", "peaceful and harmonious",
        "magical and enchanted", "celestial and cosmic", "ethereal and ghostly"
    ]
    
    # Technical qualities
    qualities = [
        "ultra-detailed", "hyper-realistic", "HDR", "8k", "32k",
        "cinematic lighting", "dramatic atmosphere", "volumetric lighting",
        "ray tracing", "photorealistic", "studio quality", "professional photography",
        "octane render", "unreal engine", "dynamic range", "atmospheric perspective"
    ]
    
    # Story elements
    stories = [
        "where time stands still", "where past meets future",
        "where reality bends", "where dimensions converge",
        "where time flows backwards", "where eternity unfolds",
        "where moments crystallize", "where infinity loops",
        "where chronology fractures", "where time spirals endlessly"
    ]

    # Construct the prompt with more variation
    prompt_structure = random.choice([
        # Structure 1: Environment-focused
        f"A {random.choice(environments)} {random.choice(times)}, featuring {random.choice(main_elements)}, {random.choice(details)}, {random.choice(details)}, {random.choice(stories)}, {random.choice(atmospheres)}, {random.choice(qualities)}, {random.choice(qualities)}",
        
        # Structure 2: Main element-focused
        f"{random.choice(main_elements)} {random.choice(times)} {random.choice(environments)}, {random.choice(details)}, {random.choice(stories)}, {random.choice(atmospheres)}, {random.choice(qualities)}, {random.choice(qualities)}",
        
        # Structure 3: Story-focused
        f"A realm {random.choice(stories)}, {random.choice(environments)}, with {random.choice(main_elements)}, {random.choice(details)}, {random.choice(atmospheres)}, {random.choice(qualities)}, {random.choice(qualities)}"
    ])
    
    prompt = f"{prompt_structure}, trending on ArtStation"
    print(f"\nGenerated prompt: {prompt}")
    return prompt

def draw_tapered_line(surface, color, start_pos, end_pos, start_width, end_width):
    """Draw a line that is wider at the start and narrower at the end"""
    angle = math.atan2(end_pos[1] - start_pos[1], end_pos[0] - start_pos[0])
    length = math.sqrt((end_pos[0] - start_pos[0])**2 + (end_pos[1] - start_pos[1])**2)
    
    # Create points for a polygon
    points = []
    for t in range(0, 101, 5):  # More points = smoother taper
        t = t / 100
        # Current width at this point
        width = start_width * (1 - t) + end_width * t
        # Position along the line
        x = start_pos[0] + (end_pos[0] - start_pos[0]) * t
        y = start_pos[1] + (end_pos[1] - start_pos[1]) * t
        # Add points perpendicular to the line
        points.append((
            x + math.cos(angle + math.pi/2) * width/2,
            y + math.sin(angle + math.pi/2) * width/2
        ))
    
    # Add points in reverse for the other side
    for t in range(100, -1, -5):
        t = t / 100
        width = start_width * (1 - t) + end_width * t
        x = start_pos[0] + (end_pos[0] - start_pos[0]) * t
        y = start_pos[1] + (end_pos[1] - start_pos[1]) * t
        points.append((
            x + math.cos(angle - math.pi/2) * width/2,
            y + math.sin(angle - math.pi/2) * width/2
        ))
    
    pygame.draw.polygon(surface, color, points)

def draw_clock_hands(hours, minutes):
    """Draw clock hands for API only"""
    api_surface.fill(GRAY)  # Fill with gray background
    
    # Draw clock circle
    pygame.draw.circle(api_surface, WHITE, CENTER, CLOCK_RADIUS, 3)
    
    # Hour hand
    hour_angle = math.radians((hours % 12 + minutes / 60) * 360 / 12 - 90)
    hour_end = (
        CENTER[0] + HOUR_HAND_LENGTH * math.cos(hour_angle),
        CENTER[1] + HOUR_HAND_LENGTH * math.sin(hour_angle)
    )
    draw_tapered_line(api_surface, WHITE, CENTER, hour_end, 24, 6)
    
    # Minute hand
    minute_angle = math.radians(minutes * 360 / 60 - 90)
    minute_end = (
        CENTER[0] + MINUTE_HAND_LENGTH * math.cos(minute_angle),
        CENTER[1] + MINUTE_HAND_LENGTH * math.sin(minute_angle)
    )
    draw_tapered_line(api_surface, WHITE, CENTER, minute_end, 16, 4)
    
    # Draw hour markers
    for hour in range(12):
        angle = math.radians(hour * 360 / 12 - 90)
        start_pos = (
            CENTER[0] + (CLOCK_RADIUS - MARKER_LENGTH) * math.cos(angle),
            CENTER[1] + (CLOCK_RADIUS - MARKER_LENGTH) * math.sin(angle)
        )
        end_pos = (
            CENTER[0] + CLOCK_RADIUS * math.cos(angle),
            CENTER[1] + CLOCK_RADIUS * math.sin(angle)
        )
        pygame.draw.line(api_surface, WHITE, start_pos, end_pos, 3)
    
    # Draw center dot
    pygame.draw.circle(api_surface, WHITE, CENTER, 10)
    
    save_debug_image(api_surface, "clockface")
    
    return api_surface

def surface_to_base64(surface):
    """Convert a pygame surface to base64 string.
    The surface should be in RGBA format with a black background and white clock hands."""
    # First ensure we're working with RGBA
    if surface.get_bitsize() != 32:
        temp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        temp.blit(surface, (0, 0))
        surface = temp

    # Convert to PIL Image
    string_image = pygame.image.tostring(surface, 'RGBA')
    pil_image = Image.frombytes('RGBA', (WIDTH, HEIGHT), string_image)
    
    # Convert to RGB with white on black background
    # This ensures the API gets a clean black and white image
    rgb_image = Image.new('RGB', pil_image.size, (0, 0, 0))
    rgb_image.paste(pil_image, mask=pil_image.split()[3])  # Use alpha as mask
    
    # Save the pre-API image for debugging
    timestamp = datetime.now().strftime("%H%M%S")
    debug_filename = f"debug_preapi_{timestamp}.png"
    rgb_image.save(debug_filename)
    print(f"Saved pre-API image to {debug_filename}")
    
    # Convert to base64
    buffered = BytesIO()
    rgb_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
        
    return img_str

def get_background_image(clock_image_base64):
    with open('api_payload.json', 'r') as f:
        payload = json.load(f)
    
    payload["prompt"] = generate_random_prompt()
    payload["alwayson_scripts"]["controlnet"]["args"][0]["image"] = clock_image_base64
    
    print("\nSending request to Stable Diffusion API...")
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        if response.status_code == 200:
            print("Received response from API")
            image_data = base64.b64decode(response.json()['images'][0])
            image = Image.open(BytesIO(image_data))
            
            save_debug_image(image, "background")
            
            return image
        print(f"Error: API request failed with status code {response.status_code}")
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        print(f"Error: Could not connect to API server: {e}")
    except Exception as e:
        print(f"Error: Unexpected error during API request: {e}")
    return None

class BackgroundUpdater:
    def __init__(self):
        self.background = None
        self.lock = threading.Lock()
        self.last_attempt = 0
        self.is_updating = False
        self.update_thread = None
    
    def _do_update(self, clock_image_base64):
        """Internal method that runs in a separate thread to update the background"""
        try:
            new_bg = get_background_image(clock_image_base64)
            if new_bg:
                with self.lock:
                    self.background = new_bg
                    print(f"Background updated at {datetime.now().strftime('%H:%M:%S')}")
        finally:
            with self.lock:
                self.is_updating = False
                self.update_thread = None
    
    def update_background(self, clock_image_base64):
        current_time = time.time()
        with self.lock:
            if self.is_updating or (current_time - self.last_attempt) < 15:
                return
            self.is_updating = True
            self.last_attempt = current_time
            
            # Create and start a new thread for the update
            self.update_thread = threading.Thread(
                target=self._do_update,
                args=(clock_image_base64,)
            )
            self.update_thread.daemon = True  # Thread will be killed when main program exits
            self.update_thread.start()
    
    def get_background(self):
        with self.lock:
            return self.background
    
    def should_update(self):
        return time.time() - self.last_attempt >= 15

background_updater = BackgroundUpdater()

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

def draw_clock_overlay(surface):
    """Draw clock face overlay with hour markers and outer circle"""
    # Draw outer circle
    pygame.draw.circle(surface, TRANSPARENT_WHITE, CENTER, CLOCK_RADIUS, 3)
    
    # Draw hour markers
    for hour in range(12):
        angle = math.radians(hour * 360 / 12 - 90)
        start_pos = (
            CENTER[0] + (CLOCK_RADIUS - MARKER_LENGTH) * math.cos(angle),
            CENTER[1] + (CLOCK_RADIUS - MARKER_LENGTH) * math.sin(angle)
        )
        end_pos = (
            CENTER[0] + CLOCK_RADIUS * math.cos(angle),
            CENTER[1] + CLOCK_RADIUS * math.sin(angle)
        )
        pygame.draw.line(surface, TRANSPARENT_WHITE, start_pos, end_pos, 3)

def main():
    print("Starting clock application...")
    print(f"Will refresh background every 15 seconds")
    print(f"API endpoint: {API_URL}")
    
    clock = pygame.time.Clock()
    running = True
    first_background_received = False
    
    # Force initial update
    now = datetime.now()
    hands_surface = draw_clock_hands(now.hour, now.minute)
    hands_base64 = surface_to_base64(hands_surface)
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
            hands_surface = draw_clock_hands(hours, minutes)
            hands_base64 = surface_to_base64(hands_surface)
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
        overlay_surface.fill((0, 0, 0, 0))
        
        # Draw clock face overlay
        draw_clock_overlay(overlay_surface)
        
        # Draw seconds hand on overlay
        seconds_angle = math.radians(seconds * 360 / 60 - 90)
        seconds_end = (
            CENTER[0] + SECOND_HAND_LENGTH * math.cos(seconds_angle),
            CENTER[1] + SECOND_HAND_LENGTH * math.sin(seconds_angle)
        )
        draw_tapered_line(overlay_surface, TRANSPARENT_WHITE, CENTER, seconds_end, 6, 2)
        
        # Draw overlay
        screen.blit(overlay_surface, (0, 0))
        
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main() 