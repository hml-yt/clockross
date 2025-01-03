import pygame
import math
from datetime import datetime, timedelta
import base64
import requests
import json
from io import BytesIO
import threading

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1280, 720

# Colors
TRANSPARENT_WHITE = (255, 255, 255, 76)  # RGBA (76 = 30% transparency)

# Create the display surface for rendering
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Clock App")

# Create a temporary surface for hour/minute hands
api_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

# Set up the clock hand dimensions
CENTER = (WIDTH // 2, HEIGHT // 2)
SECOND_HAND_LENGTH = 300
MINUTE_HAND_LENGTH = 230
HOUR_HAND_LENGTH = 180

# Background image shared between threads
background_image = None
background_lock = threading.Lock()  # Lock to ensure thread safety when updating the background

# Load the overlay image
overlay_image = pygame.image.load("overlay.png").convert_alpha()
overlay_image = pygame.transform.scale(overlay_image, (WIDTH, HEIGHT))


# Function to calculate rectangle vertices for clock hands
def get_hand_vertices(length, angle, width):
    x1 = CENTER[0] + length * math.cos(angle)
    y1 = CENTER[1] + length * math.sin(angle)
    x2 = CENTER[0] + (width / 2) * math.sin(angle)
    y2 = CENTER[1] - (width / 2) * math.cos(angle)
    x3 = CENTER[0] - (width / 2) * math.sin(angle)
    y3 = CENTER[1] + (width / 2) * math.cos(angle)
    return [(CENTER[0], CENTER[1]), (x2, y2), (x1, y1), (x3, y3)]


# Render hour/minute hands for API and return Base64
def generate_hour_minute_base64():
    # Get the current time
    now = datetime.now()
    hour = now.hour % 12
    minute = now.minute

    # Calculate angles (in radians) for hour and minute hands
    minute_angle = -math.pi / 2 + 2 * math.pi * (minute / 60)
    hour_angle = -math.pi / 2 + 2 * math.pi * ((hour + minute / 60) / 12)

    # Clear the API surface
    api_surface.fill((0, 0, 0, 255))  # Transparent background

    # Draw hour and minute hands as rectangles
    hour_vertices = get_hand_vertices(HOUR_HAND_LENGTH, hour_angle, 50)  # Hour hand width = 50
    minute_vertices = get_hand_vertices(MINUTE_HAND_LENGTH, minute_angle, 30)  # Minute hand width = 30
    pygame.draw.polygon(api_surface, (255, 255, 255), hour_vertices)  # White color for hour hand
    pygame.draw.polygon(api_surface, (255, 255, 255), minute_vertices)  # White color for minute hand

    # Save the API surface to a buffer
    buffer = BytesIO()
    pygame.image.save(api_surface, buffer, "PNG")
    buffer.seek(0)

    # Convert buffer to Base64
    base64_string = base64.b64encode(buffer.read()).decode("utf-8")
    
        # --- Debug: Save Base64 image to a file ---
    try:
        image_data = base64.b64decode(base64_string)
        with open("debug_hand_image.png", "wb") as f:
            f.write(image_data)
        print("Debug: Base64 image saved to debug_hand_image.png")
    except Exception as e:
        print(f"Error saving debug image: {e}")
    # --- End of Debug ---

    return base64_string


# Function to handle the API call in a background thread
def fetch_background():
    global background_image

    while True:
        base64_encoded_image = generate_hour_minute_base64()
        if base64_encoded_image:
            url = "http://orinputer.local:7860/sdapi/v1/txt2img"
            payload = {
                "height": 360,
                "batch_size": 1,
                "prompt": "A lush rainforest with dense foliage, cascading waterfalls, vibrant flowers, beams of sunlight piercing through the canopy, hyper-detailed, HDR, photorealistic, 8k",
                "alwayson_scripts": {
                    "controlnet": {
                        "args": [
                            {
                                "enabled": True,
                                "image": {
                                    "image": base64_encoded_image,
                                },
                                "model": "control_v11f1e_sd15_tile",
                                "resize_mode": "Just Resize",
                                "weight": 1.2,
                                "control_mode": "Balanced",
                                "guidance_start": 0.05,
                                "guidance_end": 0.95
                            }
                        ]
                    }
                },
                "sampler_name": "DPM++ 2M Karras",
                "negative_prompt": "(worst quality, low quality:1.4), watermark, signature, text",
                "steps": 12,
                "width": 640,
                "cfg_scale": 7
            }

            try:
                print("🚀 Sending request to Stable Diffusion API with ControlNet...")
                response = requests.post(
                    url=url,
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(payload)
                )
                print(f"📡 Response received with status code: {response.status_code}")
                if response.status_code == 200:
                    response_data = response.json()
                    if "images" in response_data:
                        # Decode the first image and set it as the background
                        with background_lock:
                            background_image = base64.b64decode(response_data["images"][0])
                        print("✅ Background updated.")
                else:
                    print(f"❌ Request failed. Response body: {response.text}")
            except Exception as e:
                print(f"❌ HTTP Request failed: {e}")

        # Wait 15 seconds before making the next request
        pygame.time.wait(15000)
        
# Render the second hand on top of the API response background and overlay
def render_second_hand():
    # Draw the API response background
    with background_lock:
        if background_image:
            bg_surface = pygame.image.load(BytesIO(background_image))
            bg_surface = pygame.transform.scale(bg_surface, (WIDTH, HEIGHT))
            screen.blit(bg_surface, (0, 0))

    # Draw the overlay image
    screen.blit(overlay_image, (0, 0))

    # Get the current time
    now = datetime.now()
    second = now.second

    # Calculate the angle (in radians) for the second hand
    second_angle = -math.pi / 2 + 2 * math.pi * (second / 60)

    # Draw semi-transparent second hand (line)
    temp_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.line(temp_surface, TRANSPARENT_WHITE, CENTER, (
        CENTER[0] + SECOND_HAND_LENGTH * math.cos(second_angle),
        CENTER[1] + SECOND_HAND_LENGTH * math.sin(second_angle)
    ), 2)
    screen.blit(temp_surface, (0, 0))

    # Update the display
    pygame.display.flip()


# Start the background thread for fetching the API response
background_thread = threading.Thread(target=fetch_background, daemon=True)
background_thread.start()

# Main Pygame loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Render the second hand with the current background
    render_second_hand()

# Quit Pygame
pygame.quit()