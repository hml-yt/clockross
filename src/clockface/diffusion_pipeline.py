import torch
import gc
import time
import threading
from diffusers import AutoencoderKL, ControlNetModel, StableDiffusionControlNetPipeline, DPMSolverMultistepScheduler
from compel import Compel
from ..config import Config

class DiffusionPipeline:
    def __init__(self, debug=False):
        self.config = Config()
        self.debug = debug
        self.device = self._get_device()
        self.pipe = None
        self.is_loading = False
        self.reload_complete_callback = None
        self.reload_error_callback = None
        
        if self.debug:
            print(f"Using device: {self.device}")
        
        # Initialize pipeline
        self._initialize_pipeline()
    
    def _get_device(self):
        """Determine the appropriate device (CUDA, MPS, or CPU)"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def _empty_cache(self):
        """Properly clean up Python and device memory"""
        gc.collect()
        if self.device == "cuda":
            torch.cuda.empty_cache()
        elif self.device == "mps":
            # MPS doesn't have an explicit cache clearing mechanism
            # but we can force a sync point
            if torch.backends.mps.is_available():
                torch.mps.synchronize()
        if self.debug:
            print("Memory cache cleared")

    def _cleanup_pipeline(self):
        """Clean up the existing pipeline to free GPU memory"""
        if hasattr(self, 'pipe') and self.pipe is not None:
            try:
                del self.pipe
                self.pipe = None
                self._empty_cache()
                time.sleep(1)  # Small delay to ensure cleanup
            except Exception as e:
                if self.debug:
                    print(f"Error cleaning up pipeline: {e}")

    def _initialize_pipeline(self):
        """Initialize the Stable Diffusion pipeline with ControlNet"""
        if self.debug:
            print("Initializing Stable Diffusion pipeline...")
        
        self._load_pipeline()

    def _load_pipeline(self):
        """Load the pipeline with current configuration"""
        # Load VAE
        vae = AutoencoderKL.from_pretrained(
            self.config.render['models']['vae'],
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device)
        
        # Load ControlNet
        controlnet = ControlNetModel.from_pretrained(
            self.config.render['models']['controlnet'],
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device)
        
        # Load main model
        self.pipe = StableDiffusionControlNetPipeline.from_single_file(
            self.config.render['checkpoint'],
            controlnet=controlnet,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            safety_checker=None,
            generator=torch.Generator(device=self.device),
            vae=vae
        ).to(self.device)

        # Only enable CPU offload for CUDA devices
        if self.device == "cuda":
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
            
            # Clean up existing pipeline
            if self.debug:
                print("Cleaning up old pipeline...")
            self._cleanup_pipeline()
            
            if self.debug:
                print("Loading new pipeline...")
            self._load_pipeline()
            
            if self.debug:
                print("Pipeline reload complete")
            
            # Notify completion if callback is set
            if self.reload_complete_callback:
                self.reload_complete_callback()
        except Exception as e:
            if self.reload_error_callback:
                self.reload_error_callback(e)
            if self.debug:
                print(f"Error reloading pipeline: {e}")

    def reload(self, complete_callback=None, error_callback=None):
        """Reload the pipeline with new configuration in a separate thread"""
        self.is_loading = True
        def wrapped_callback():
            self.is_loading = False
            if complete_callback:
                complete_callback()
        self.reload_complete_callback = wrapped_callback
        self.reload_error_callback = error_callback
        reload_thread = threading.Thread(target=self._do_reload_pipeline)
        reload_thread.daemon = True
        reload_thread.start()

    def generate(self, source_image, prompt, negative_prompt=None):
        """Generate an image using the pipeline"""
        if self.pipe is None:
            raise RuntimeError("Pipeline not initialized")

        # Get generation settings from config
        gen_config = self.config.render['generation']
        
        # Generate random seed
        generator = torch.Generator(device=self.device)
        seed = generator.initial_seed()
        
        # Compel prompt
        compel = Compel(tokenizer=self.pipe.tokenizer, text_encoder=self.pipe.text_encoder)
        conditioning = compel(prompt)

        # Handle negative prompt
        if negative_prompt is None:
            negative_prompt = self.config.prompts['negative_prompt']
        negative_conditioning = compel(negative_prompt)
        
        # Pad conditioning tensors
        [conditioning, negative_conditioning] = compel.pad_conditioning_tensors_to_same_length([conditioning, negative_conditioning])
        
        # Move conditioning tensors to the correct device
        conditioning = conditioning.to(self.device)
        negative_conditioning = negative_conditioning.to(self.device)
        
        # Generate image
        result = self.pipe(
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
        )

        return result.images[0], seed 