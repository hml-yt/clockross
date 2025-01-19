import time
import json
import torch
import gc
from PIL import Image
from datetime import datetime
import threading
from diffusers import AutoencoderKL, ControlNetModel, StableDiffusionControlNetPipeline, DPMSolverMultistepScheduler
from diffusers.schedulers import AysSchedules
from .prompt_generator import PromptGenerator
from ..utils.image_utils import save_debug_image
from ..config import Config
import random
import os
import pygame

class BackgroundUpdater:
    def __init__(self, debug=False):
        self.config = Config()
        self.debug = debug
        self.surface_manager = None
        self.current_color = (255, 255, 255, self.config.clock['overlay_opacity'])  # Default color
        self.previous_color = None
        self.transition_start = 0
        self.transition_duration = self.config.animation['transition_duration']
        self.update_interval = self.config.animation['background_update_interval']
        self.lock = threading.Lock()
        self.last_attempt = 0
        self.is_updating = False
        self.update_thread = None
        self.prompt_generator = PromptGenerator()
        
        # Initialize Diffusers pipeline
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Initialize the Stable Diffusion pipeline with ControlNet"""
        if self.debug:
            print("Initializing Stable Diffusion pipeline...")
        
        self._load_pipeline()

    def _empty_cache(self):
        """Properly clean up Python and CUDA memory"""
        gc.collect()
        torch.cuda.empty_cache()
        if self.debug:
            print("Memory cache cleared")

    def _cleanup_pipeline(self):
        """Clean up the existing pipeline to free GPU memory"""
        if hasattr(self, 'pipe'):
            try:
                # Delete the pipeline components explicitly
                if hasattr(self.pipe, 'vae'):
                    del self.pipe.vae
                if hasattr(self.pipe, 'controlnet'):
                    del self.pipe.controlnet
                if hasattr(self.pipe, 'scheduler'):
                    del self.pipe.scheduler
                # Delete the main pipeline
                del self.pipe
                # Clean up memory
                self._empty_cache()
            except Exception as e:
                if self.debug:
                    print(f"Error cleaning up pipeline: {e}")

    def _load_pipeline(self):
        """Load the pipeline with current configuration"""
        # Load VAE
        vae = AutoencoderKL.from_single_file(
            self.config.render['models']['vae'],
            torch_dtype=torch.float16
        ).to('cuda')
        
        # Load ControlNet
        controlnet = ControlNetModel.from_single_file(
            self.config.render['models']['controlnet'],
            torch_dtype=torch.float16
        ).to('cuda')
        
        # Load sampling schedule
        sampling_schedule = AysSchedules["StableDiffusionTimesteps"]
        sigmas = AysSchedules["StableDiffusionSigmas"]
        
        # Load main model
        self.pipe = StableDiffusionControlNetPipeline.from_single_file(
            self.config.render['checkpoint'],
            controlnet=controlnet,
            torch_dtype=torch.float16,
            safety_checker=None,
            generator=torch.Generator(device='cuda'),
            timesteps=sampling_schedule,
            sigmas=sigmas,
            vae=vae
        ).to('cuda')
        
        # Set up scheduler
        scheduler = DPMSolverMultistepScheduler.from_config(
            self.pipe.scheduler.config,
            algorithm_type="dpmsolver++",
            timestep_spacing="trailing",
            use_karras_sigmas=True
        )
        self.pipe.scheduler = scheduler
        
        if self.debug:
            print("Pipeline initialized successfully")

    def _do_reload_pipeline(self):
        """Internal method to handle the actual pipeline reload"""
        if self.debug:
            print("Starting pipeline reload...")
            
        # Force cleanup of any ongoing generation
        if self.is_updating and self.update_thread:
            self.is_updating = False
            self.update_thread = None
        
        # Now safe to cleanup and reload
        if self.debug:
            print("Cleaning up old pipeline...")
        self._cleanup_pipeline()
        if self.debug:
            print("Loading new pipeline...")
        self._load_pipeline()
        
        if self.debug:
            print("Pipeline reload complete")
        
        # Notify completion if callback is set
        if hasattr(self, 'reload_complete_callback') and self.reload_complete_callback:
            self.reload_complete_callback()

    def reload_pipeline(self, complete_callback=None):
        """Reload the pipeline with new configuration in a separate thread"""
        self.reload_complete_callback = complete_callback
        reload_thread = threading.Thread(target=self._do_reload_pipeline)
        reload_thread.daemon = True
        reload_thread.start()

    def set_surface_manager(self, surface_manager):
        """Set the surface manager instance"""
        self.surface_manager = surface_manager
    
    def _extract_dominant_color(self, pil_image):
        """Extract the brightest color from the image (likely the clock hands/markers)"""
        # Convert to RGB if not already
        rgb_image = pil_image.convert('RGB')
        # Resize to speed up processing
        rgb_image.thumbnail((100, 100))
        
        # Get pixel data
        pixels = list(rgb_image.getdata())
        
        # Calculate brightness for each pixel and find the brightest one
        brightest_pixel = max(pixels, key=lambda p: sum(p))
        
        # Make it transparent according to config
        return (*brightest_pixel, self.config.clock['overlay_opacity'])
    
    def _get_background_image(self, hands_surface):
        """Generate a new background image using Stable Diffusion with ControlNet"""
        try:
            # Convert pygame surface (RGB) to PIL Image
            array = pygame.surfarray.array3d(hands_surface)
            # Ensure array is in the correct shape (height, width, channels)
            array = array.transpose(1, 0, 2)
            source_image = Image.fromarray(array)
            
            if self.debug:
                save_debug_image(source_image, "prerender")
            
            # Generate prompt
            prompt = self.prompt_generator.generate()
            
            if self.debug:
                print(f"\nGenerating image with prompt: {prompt}")
            
            # Get generation settings from config
            gen_config = self.config.render['generation']
            
            # Generate random seed
            seed = random.randint(0, 2**32 - 1)
            generator = torch.Generator(device='cuda').manual_seed(seed)
            
            # Generate image
            image = self.pipe(
                prompt,
                image=source_image,
                height=self.config.render['height'],
                width=self.config.render['width'],
                negative_prompt="asian, (worst quality, low quality:1.4), watermark, signature, flower, facial marking, (women:1.2), (female:1.2), blue jeans, 3d, render, doll, plastic, blur, haze, monochrome, b&w, text, (ugly:1.2), unclear eyes, no arms, bad anatomy, cropped, censoring, asymmetric eyes, bad anatomy, bad proportions, cropped, cross-eyed, deformed, extra arms, extra fingers, extra limbs, fused fingers, jpeg artifacts, malformed, mangled hands, misshapen body, missing arms, missing fingers, missing hands, missing legs, poorly drawn, tentacle finger, too many arms, too many fingers, (worst quality, low quality:1.4), watermark, signature,illustration,painting, anime,cartoon",
                controlnet_conditioning_scale=gen_config['controlnet_conditioning_scale'],
                num_inference_steps=gen_config['num_inference_steps'],
                guidance_scale=gen_config['guidance_scale'],
                control_guidance_start=gen_config['control_guidance_start'],
                control_guidance_end=gen_config['control_guidance_end'],
                generator=generator
            ).images[0]
            
            if self.debug:
                save_debug_image(image, "background")
                print("Image generated successfully")
            
            # Store generation metadata
            metadata = {
                "prompt": prompt,
                "seed": seed,
                "checkpoint": os.path.basename(self.config.render['checkpoint']),
                "timestamp": datetime.now().isoformat(),
                "generation_config": gen_config
            }
            
            # Update render request in surface manager
            if self.surface_manager:
                self.surface_manager.update_render_request(metadata)
            
            return image
            
        except Exception as e:
            print(f"Error: Failed to generate image: {e}")
            return None
    
    def _do_update(self, hands_surface):
        """Internal method that runs in a separate thread to update the background"""
        try:
            new_bg = self._get_background_image(hands_surface)
            if new_bg:
                with self.lock:
                    # Store the current color as previous for transition
                    self.previous_color = self.current_color
                    self.current_color = self._extract_dominant_color(new_bg)
                    self.transition_start = time.time()
                    
                    # Update background in surface manager
                    if self.surface_manager:
                        self.surface_manager.update_background(new_bg)
                    
                    if self.debug:
                        print(f"Background updated at {datetime.now().strftime('%H:%M:%S')}")
                        print(f"New brightest color: RGB{self.current_color[:3]} (15% opacity)")
        finally:
            with self.lock:
                self.is_updating = False
                self.update_thread = None
    
    def _interpolate_color(self, color1, color2, progress):
        """Interpolate between two colors"""
        if not color1 or not color2:
            return color2 or color1
        return tuple(
            int(c1 + (c2 - c1) * progress)
            for c1, c2 in zip(color1, color2)
        )
    
    def get_dominant_color(self):
        """Get the current dominant color with transition"""
        with self.lock:
            if not self.previous_color:
                return self.current_color
            
            # Calculate transition progress
            progress = min(1.0, (time.time() - self.transition_start) / self.transition_duration)
            
            # Interpolate between previous and current color
            return self._interpolate_color(self.previous_color, self.current_color, progress)
    
    def update_background(self, hands_surface):
        """Start a background update if conditions are met"""
        current_time = time.time()
        with self.lock:
            if self.is_updating or (current_time - self.last_attempt) < self.update_interval:
                return
            self.is_updating = True
            self.last_attempt = current_time
            
            # Create and start a new thread for the update
            self.update_thread = threading.Thread(
                target=self._do_update,
                args=(hands_surface,)
            )
            self.update_thread.daemon = True  # Thread will be killed when main program exits
            self.update_thread.start()
    
    def should_update(self):
        """Check if it's time for a background update"""
        return time.time() - self.last_attempt >= self.update_interval 