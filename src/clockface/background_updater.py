import time
import os
import threading
from datetime import datetime

import pygame
from PIL import Image

from .prompt_generator import PromptGenerator
from .diffusion_pipeline import DiffusionPipeline
from ..utils.image_utils import save_debug_image
from ..config import Config

class BackgroundUpdater:
    # Watchdog timeout - if a thread runs longer than this, consider it hung
    WATCHDOG_TIMEOUT = 120  # seconds
    # Number of generations between GPU cache cleanup
    CACHE_CLEANUP_INTERVAL = 50
    # Maximum consecutive failures before forcing a longer backoff
    MAX_CONSECUTIVE_FAILURES = 3
    # Backoff multiplier after max failures (multiply update_interval by this)
    FAILURE_BACKOFF_MULTIPLIER = 3
    
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
        self.update_thread_start_time = 0  # Track when thread started for watchdog
        self.prompt_generator = PromptGenerator()
        
        # Reliability tracking
        self.generation_count = 0  # Track generations for periodic cleanup
        self.consecutive_failures = 0  # Track failures for backoff logic
        
        # Initialize pipeline
        self.pipeline = DiffusionPipeline(debug=debug)
    
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
        start_time = time.time()
        generation_start = None
        generation_end = None
        enhancement_time = 0.0
        
        try:
            # Convert pygame surface (RGB) to PIL Image
            array = pygame.surfarray.array3d(hands_surface)
            # Ensure array is in the correct shape (height, width, channels)
            array = array.transpose(1, 0, 2)
            source_image = Image.fromarray(array)
            
            # Generate prompt (this includes queueing and waiting for enhancement)
            prompt, enhancement_time = self.prompt_generator.generate()
            
            if self.debug:
                save_debug_image(source_image, "prerender")
                print(f"\nGenerating image with prompt: {prompt}")
            
            # Generate image using pipeline
            generation_start = time.time()
            image, seed = self.pipeline.generate(source_image, prompt)
            generation_end = time.time()
            
            if self.debug:
                save_debug_image(image, "background")
                print("Image generated successfully")
            
            # Store generation metadata
            metadata = {
                "prompt": prompt,
                "seed": seed,
                "checkpoint": os.path.basename(self.config.render['checkpoint']),
                "timestamp": datetime.now().isoformat(),
                "generation_config": self.config.render['generation']
            }
            
            # Update render request in surface manager
            if self.surface_manager:
                self.surface_manager.update_render_request(metadata)
            
            # Log timing information
            total_time = time.time() - start_time
            generation_time = generation_end - generation_start if generation_start and generation_end else 0
            # Other time is what's left after generation (enhancement happens concurrently)
            other_time = total_time - generation_time
            print(f"Background update completed in {total_time:.2f}s (prompt enhancement: {enhancement_time:.2f}s, generation: {generation_time:.2f}s, other: {other_time:.2f}s)")
            
            return image
            
        except Exception as e:
            total_time = time.time() - start_time
            print(f"Background update failed after {total_time:.2f}s: {e}")
            return None
    
    def _do_update(self, hands_surface):
        """Internal method that runs in a separate thread to update the background"""
        success = False
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
                    
                    # Track successful generation
                    self.generation_count += 1
                    self.consecutive_failures = 0  # Reset failure counter on success
                    success = True
                    
                    if self.debug:
                        print(f"Background updated at {datetime.now().strftime('%H:%M:%S')}")
                        print(f"New brightest color: RGB{self.current_color[:3]} (15% opacity)")
                        print(f"Generation count: {self.generation_count}")
                
                # Periodic GPU cache cleanup (outside lock to avoid blocking)
                if self.generation_count % self.CACHE_CLEANUP_INTERVAL == 0:
                    self._periodic_cleanup()
            else:
                # Generation returned None (failed)
                with self.lock:
                    self.consecutive_failures += 1
                    if self.debug:
                        print(f"Generation failed. Consecutive failures: {self.consecutive_failures}")
        except Exception as e:
            # Catch any unexpected errors in the update thread
            print(f"Unexpected error in background update thread: {e}")
            with self.lock:
                self.consecutive_failures += 1
        finally:
            with self.lock:
                self.is_updating = False
                self.update_thread = None
                self.update_thread_start_time = 0
    
    def _periodic_cleanup(self):
        """Perform periodic GPU memory cleanup to prevent fragmentation"""
        try:
            if self.debug:
                print(f"Performing periodic GPU cache cleanup (every {self.CACHE_CLEANUP_INTERVAL} generations)")
            self.pipeline._empty_cache()
        except Exception as e:
            print(f"Error during periodic cleanup: {e}")
    
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
    
    def _check_and_recover_stuck_thread(self, current_time):
        """Check if update thread is stuck and recover if necessary.
        
        Returns True if recovery was performed (caller should proceed with new update).
        Returns False if thread is still legitimately running.
        Must be called with self.lock held.
        """
        if not self.is_updating:
            return False
            
        # Check if thread exists and is still alive
        if self.update_thread is not None and self.update_thread.is_alive():
            # Thread is running - check if it's exceeded the watchdog timeout
            elapsed = current_time - self.update_thread_start_time
            if elapsed > self.WATCHDOG_TIMEOUT:
                print(f"WARNING: Background update thread exceeded watchdog timeout ({elapsed:.1f}s > {self.WATCHDOG_TIMEOUT}s)")
                print("Forcing recovery - thread will be orphaned (daemon thread will be cleaned up on exit)")
                # Force reset the state - the old thread is orphaned but will eventually die
                # or be cleaned up when the process exits (it's a daemon thread)
                self.is_updating = False
                self.update_thread = None
                self.update_thread_start_time = 0
                self.consecutive_failures += 1
                # Perform emergency cache cleanup
                try:
                    self.pipeline._empty_cache()
                except Exception as e:
                    print(f"Error during emergency cache cleanup: {e}")
                return True
            else:
                # Thread is still running within timeout - don't interfere
                return False
        else:
            # Thread reference exists but thread is dead, or is_updating is True but no thread
            # This is an inconsistent state - recover
            print("WARNING: Inconsistent thread state detected (is_updating=True but thread dead/missing)")
            self.is_updating = False
            self.update_thread = None
            self.update_thread_start_time = 0
            return True
    
    def _get_effective_update_interval(self):
        """Get the effective update interval, accounting for failure backoff.
        
        Must be called with self.lock held.
        """
        if self.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
            backoff_interval = self.update_interval * self.FAILURE_BACKOFF_MULTIPLIER
            if self.debug:
                print(f"Applying failure backoff: {backoff_interval}s (normal: {self.update_interval}s)")
            return backoff_interval
        return self.update_interval

    def update_background(self, hands_surface):
        """Start a background update if conditions are met"""
        current_time = time.time()
        with self.lock:
            # First, check for and recover from stuck threads (watchdog)
            self._check_and_recover_stuck_thread(current_time)
            
            # Get effective interval (may be longer if we've had consecutive failures)
            effective_interval = self._get_effective_update_interval()
            
            # Don't update if we're already updating or if the pipeline is loading
            if self.is_updating or self.pipeline.is_loading:
                return
            
            # Check if enough time has passed since last attempt
            if (current_time - self.last_attempt) < effective_interval:
                return
                
            self.is_updating = True
            self.last_attempt = current_time
            self.update_thread_start_time = current_time  # Track for watchdog
            
            # Create and start a new thread for the update
            self.update_thread = threading.Thread(
                target=self._do_update,
                args=(hands_surface,)
            )
            self.update_thread.daemon = True  # Thread will be killed when main program exits
            self.update_thread.start()
    
    def should_update(self):
        """Check if it's time for a background update"""
        with self.lock:
            effective_interval = self._get_effective_update_interval()
            return time.time() - self.last_attempt >= effective_interval
    
    def reload_pipeline(self, complete_callback=None, error_callback=None):
        """Reload the pipeline with new configuration"""
        self.pipeline.reload(complete_callback, error_callback) 
