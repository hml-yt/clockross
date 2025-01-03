import requests
import json
import base64


def encode_image_to_base64(image_path):
    """Encode an image file to a Base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            base64_string = base64.b64encode(image_file.read()).decode("utf-8")
        print(f"✅ Successfully encoded {image_path} to Base64.")
        return base64_string
    except Exception as e:
        print(f"❌ Failed to encode image: {e}")
        return None


def save_image(base64_string, file_name):
    """Save a base64 encoded image to a file."""
    try:
        image_data = base64.b64decode(base64_string)
        with open(file_name, "wb") as image_file:
            image_file.write(image_data)
        print(f"✅ Image saved as {file_name}")
    except Exception as e:
        print(f"❌ Failed to save image: {e}")


def send_request(url, payload):
    print("🚀 Sending request to Stable Diffusion API with ControlNet...")
    try:
        response = requests.post(
            url=url,
            headers={
                "Content-Type": "application/json",
            },
            data=json.dumps(payload)
        )

        print(f"📡 Response received with status code: {response.status_code}")
        if response.status_code == 200:
            try:
                response_data = response.json()
                if "images" in response_data:
                    print(f"🔍 Found {len(response_data['images'])} image(s) in the response. Saving...")
                    for i, base64_image in enumerate(response_data["images"]):
                        file_name = f"generated_image_{i + 1}.png"
                        save_image(base64_image, file_name)
                else:
                    print("⚠️ No 'images' key found in the response.")
            except json.JSONDecodeError:
                print("❌ Failed to decode JSON response. Raw response:", response.text)
        else:
            print(f"❌ Request failed. Response body: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP Request failed: {e}")


# Input image path for ControlNet
input_image_path = "clock.png"  # Replace with your image path
my_base64_encoded_image = encode_image_to_base64(input_image_path)

if my_base64_encoded_image:
    # Payload and URL
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
                            "image": my_base64_encoded_image
                        },
                        "model": "control_v11f1e_sd15_tile",
                        "resize_mode": "Crop and Resize",  # Other options: "Envelope (Outer Fit)", "Scale to Fit (Inner Fit)", "Just Resize"
                        "weight": 1.2,  # Control image weight
                        "control_mode": "Balanced",  # Options: "Balanced", "My prompt is more important", "ControlNet is more important"
                        "guidance_start": 0.05,  # Starting control step
                        "guidance_end": 0.95  # Ending control step
                    }
                ]
            }
        },
        "sampler_name": "DPM++ 2M Karras",
        "negative_prompt": "asian, (worst quality, low quality:1.4), watermark, signature, flower, facial marking, (women:1.2), (female:1.2), blue jeans, 3d, render, doll, plastic, blur, haze, monochrome, b&w, text, (ugly:1.2), unclear eyes, no arms, bad anatomy, cropped, censoring, asymmetric eyes, bad anatomy, bad proportions, cropped, cross-eyed, deformed, extra arms, extra fingers, extra limbs, fused fingers, jpeg artifacts, malformed, mangled hands, misshapen body, missing arms, missing fingers, missing hands, missing legs, poorly drawn, tentacle finger, too many arms, too many fingers, (worst quality, low quality:1.4), watermark, signature, illustration, painting, anime, cartoon",
        "steps": 12,
        "width": 640,
        "cfg_scale": 7
    }

    # Call the function
    send_request(url, payload)
else:
    print("❌ Could not proceed without a valid base64 encoded input image.")