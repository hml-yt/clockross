import time
import json
import torch
import gc
from PIL import Image
from datetime import datetime
import threading
from diffusers import AutoencoderKL, ControlNetModel, StableDiffusionControlNetPipeline, DPMSolverMultistepScheduler
from diffusers.schedulers import AysSchedules
from compel import Compel
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
        self.is_loading_pipeline = False
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
                # Delete the main pipeline
                del self.pipe
                self.pipe = None
                # Clean up memory
                self._empty_cache()
                # Add small delay to ensure cleanup
                time.sleep(1)
            except Exception as e:
                if self.debug:
                    print(f"Error cleaning up pipeline: {e}")

    def _load_pipeline(self):
        """Load the pipeline with current configuration"""
        # Load VAE
        vae = AutoencoderKL.from_pretrained(
            self.config.render['models']['vae'],
            torch_dtype=torch.float16
        ).to('cuda')
        
        # Load ControlNet
        controlnet = ControlNetModel.from_pretrained(
            self.config.render['models']['controlnet'],
            torch_dtype=torch.float16
        ).to('cuda')
        
        # Load main model
        self.pipe = StableDiffusionControlNetPipeline.from_single_file(
            self.config.render['checkpoint'],
            controlnet=controlnet,
            torch_dtype=torch.float16,
            safety_checker=None,
            generator=torch.Generator(device='cuda'),
            vae=vae
        ).to('cuda')
        self.pipe.enable_model_cpu_offload()
        
        # Apply CLIP skip by truncating layers
        total_layers = len(self.pipe.text_encoder.text_model.encoder.layers)
        clip_skip = self.config.render.get('clip_skip', 1)
        layers_to_keep = total_layers - (clip_skip - 1)
        
        if self.debug:
            print(f"Total CLIP layers: {total_layers}, keeping first {layers_to_keep} layers (clip_skip={clip_skip})")
        
        if clip_skip > 1:
            self.pipe.text_encoder.text_model.encoder.layers = self.pipe.text_encoder.text_model.encoder.layers[:layers_to_keep]

        # Set up scheduler
        scheduler = DPMSolverMultistepScheduler.from_config(
            self.pipe.scheduler.config,
            algorithm_type="dpmsolver++",
            timestep_spacing="trailing",
            use_karras_sigmas=True,
        )
        self.pipe.scheduler = scheduler
        
        if self.debug:
            print("Pipeline initialized successfully")

    def _do_reload_pipeline(self):
        """Internal method to handle the actual pipeline reload"""
        try:
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
        except Exception as e:
            if hasattr(self, 'reload_error_callback') and self.reload_error_callback:
                self.reload_error_callback(e)
            if self.debug:
                print(f"Error reloading pipeline: {e}")

    def reload_pipeline(self, complete_callback=None, error_callback=None):
        """Reload the pipeline with new configuration in a separate thread"""
        self.is_loading_pipeline = True
        def wrapped_callback():
            self.is_loading_pipeline = False
            if complete_callback:
                complete_callback()
        self.reload_complete_callback = wrapped_callback
        self.reload_error_callback = error_callback
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
            
            # Generate prompt
            prompt = self.prompt_generator.generate()
            
            if self.debug:
                save_debug_image(source_image, "prerender")
                print(f"\nGenerating image with prompt: {prompt}")
            
            # Get generation settings from config
            gen_config = self.config.render['generation']
            
            # Generate random seed
            generator = torch.Generator(device='cuda')
            seed = generator.initial_seed()
            
            # Compel prompt
            compel = Compel(tokenizer=self.pipe.tokenizer, text_encoder=self.pipe.text_encoder)
            conditioning = compel(prompt)

            negative_conditioning = compel(self.config.prompts['negative_prompt'])
            [conditioning, negative_conditioning] = compel.pad_conditioning_tensors_to_same_length([conditioning, negative_conditioning])
                        
            # Generate image
            image = self.pipe(
                prompt_embeds=conditioning,
                negative_prompt_embeds=negative_conditioning,
                image=source_image,
                height=self.config.render['height'],
                width=self.config.render['width'],
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
            # Don't update if we're already updating or if the pipeline is loading
            if self.is_updating or self.is_loading_pipeline or (current_time - self.last_attempt) < self.update_interval:
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
