from os import times
import torch
import time
from PIL import Image
from diffusers import AutoencoderKL, ControlNetModel, StableDiffusionControlNetPipeline, DPMSolverMultistepScheduler
from diffusers.utils import load_image
from prompt_generator import PromptGenerator

vae = AutoencoderKL.from_single_file(
    "models/vae-ft-mse-840000-ema-pruned.safetensors", torch_dtype=torch.float16
).to('cuda')

controlnet = ControlNetModel.from_single_file(
    "models/control_v11f1e_sd15_tile.safetensors", torch_dtype=torch.float16
).to('cuda')

pipe = StableDiffusionControlNetPipeline.from_single_file(
    "models/abstractPhoto_abcevereMix.safetensors",
    controlnet=controlnet,
    torch_dtype=torch.float16,
    safety_checker=None,
    vae=vae
).to('cuda')

scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config, use_karras_sigmas=True
)
pipe.scheduler = scheduler

source_image = load_image('sample_clock.png')

prompt_generator = PromptGenerator()
negative_prompt = "asian, (worst quality, low quality:1.4), watermark, signature, flower, facial marking, (women:1.2), (female:1.2), blue jeans, 3d, render, doll, plastic, blur, haze, monochrome, b&w, text, (ugly:1.2), unclear eyes, no arms, bad anatomy, cropped, censoring, asymmetric eyes, bad anatomy, bad proportions, cropped, cross-eyed, deformed, extra arms, extra fingers, extra limbs, fused fingers, jpeg artifacts, malformed, mangled hands, misshapen body, missing arms, missing fingers, missing hands, missing legs, poorly drawn, tentacle finger, too many arms, too many fingers, (worst quality, low quality:1.4), watermark, signature,illustration,painting, anime,cartoon"

# Store generation times
generation_times = []

# Generate 10 images
for i in range(10):
    print(f"\nGenerating image {i+1}/10...")
    start_time = time.time()
    
    # Generate a unique prompt for each image
    prompt = prompt_generator.generate()
    
    image = pipe(prompt,
                image=source_image,
                height=360,
                width=640,
                negative_prompt=negative_prompt,
                controlnet_conditioning_scale=1.0,
                num_inference_steps=12,
                guidance_scale=7,
                control_guidance_start=0.05,
                control_guidance_end=0.9,
                ).images[0]
    
    generation_time = time.time() - start_time
    generation_times.append(generation_time)
    print(f"Generation time: {generation_time:.2f} seconds")
    
    # Save the image with a numbered suffix
    image.save(f"output_{i+1}.png")

# Calculate and print average time for last 5 images
last_5_avg = sum(generation_times[-5:]) / 5
print(f"\nAll images generated successfully!")
print(f"Average generation time for last 5 images: {last_5_avg:.2f} seconds") 