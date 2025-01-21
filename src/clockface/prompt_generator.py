import random
from abc import ABC, abstractmethod
from ..config import Config
from transformers import pipeline
from ..utils.device_utils import get_best_device
import threading
import queue
import time

class PromptStrategy(ABC):
    """Abstract base class for prompt generation strategies"""
    def __init__(self, config):
        self.config = config
        self.prompt_config = config.prompts

    @abstractmethod
    def generate(self, theme, description, style, style_details):
        """Generate a prompt using the specific strategy"""
        pass

class ClassicPromptStrategy(PromptStrategy):
    """Classic prompt generation strategy using random selection and combination"""
    def generate(self, theme, description, style, style_details):
        selected_details = random.sample(style_details['details'], k=random.randint(2, 4))
        selected_resolutions = random.sample(self.prompt_config['resolutions'], k=random.randint(1, len(self.prompt_config['resolutions'])))
        selected_award = random.choice(style_details['awards'])
        
        return f"{theme}, {description}, {', '.join(selected_details)}, {', '.join(selected_resolutions)}, {selected_award}"

class EnhancedPromptStrategy(PromptStrategy):
    """AI-enhanced prompt generation strategy using language model"""
    def __init__(self, config):
        super().__init__(config)
        self.prompt_extender = None
        self.prompt_queue = queue.Queue()
        self.enhanced_prompts = queue.Queue()
        self.enhancer_thread = None
        self.is_running = False
        self.is_enhancing = threading.Event()  # Track if enhancement is in progress
        self._start_enhancer_thread()
    
    def _start_enhancer_thread(self):
        """Start the background thread for prompt enhancement"""
        if not self.is_running:
            self.is_running = True
            self.enhancer_thread = threading.Thread(target=self._enhance_prompts_worker, daemon=True)
            self.enhancer_thread.start()
    
    def _enhance_prompts_worker(self):
        """Worker thread that processes prompts in the background"""
        while self.is_running:
            try:
                base_prompt = self.prompt_queue.get(timeout=1.0)
                self.is_enhancing.set()  # Mark enhancement as in progress
                
                extender = self._get_prompt_extender()
                enhancer_config = self.prompt_config['enhancer']
                
                enhanced_prompt = extender(
                    base_prompt,
                    max_length=enhancer_config['max_length'],
                    max_time=enhancer_config['max_time'],
                    num_return_sequences=enhancer_config['num_return_sequences'],
                    temperature=enhancer_config['temperature'],
                    top_p=enhancer_config['top_p'],
                    do_sample=enhancer_config['do_sample'],
                    truncation=True
                )[0]['generated_text']
                
                self.enhanced_prompts.put(enhanced_prompt)
                self.prompt_queue.task_done()
                self.is_enhancing.clear()  # Mark enhancement as complete
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error enhancing prompt: {e}")
                # Put the original prompt back in case of error
                self.enhanced_prompts.put(base_prompt)
                self.prompt_queue.task_done()
                self.is_enhancing.clear()  # Mark enhancement as complete even on error
    
    def _get_prompt_extender(self):
        if self.prompt_extender is None:
            enhancer_config = self.prompt_config['enhancer']
            self.prompt_extender = pipeline(
                "text-generation",
                model=enhancer_config['model'],
                device=get_best_device()
            )
        return self.prompt_extender
    
    def generate(self, theme, description, style, style_details):
        """Generate a prompt using the AI-enhanced strategy"""
        base_prompt = f"{style} of {theme}, {description}"
        
        # Queue the base prompt for enhancement
        self.prompt_queue.put(base_prompt)
        
        # Wait for enhanced prompt with a timeout
        try:
            enhanced_prompt = self.enhanced_prompts.get(timeout=self.prompt_config['enhancer']['max_time'] + 1.0)
            self.enhanced_prompts.task_done()
            return enhanced_prompt
        except queue.Empty:
            print("Warning: Prompt enhancement timed out, using base prompt")
            return base_prompt
    
    def is_ready(self):
        """Check if the prompt generator is ready (not currently enhancing a prompt)"""
        return not self.is_enhancing.is_set()
    
    def __del__(self):
        """Cleanup when the object is destroyed"""
        self.is_running = False
        if self.enhancer_thread and self.enhancer_thread.is_alive():
            self.enhancer_thread.join(timeout=1.0)

class PromptStrategyFactory:
    """Factory class for creating prompt generation strategies"""
    @staticmethod
    def create_strategy(config):
        use_enhanced = config.prompts.get('use_enhanced_prompts', False)
        return EnhancedPromptStrategy(config) if use_enhanced else ClassicPromptStrategy(config)

class PromptGenerator:
    """Main prompt generator class using strategy pattern"""
    def __init__(self):
        self.config = Config()
        self.strategy = PromptStrategyFactory.create_strategy(self.config)
        self.prompt_config = self.config.prompts

    def generate(self):
        """Generate a random prompt using the selected strategy"""
        theme = random.choice(self.prompt_config['themes'])
        description = random.choice(self.prompt_config['descriptions'])
        style = random.choice(self.prompt_config['enabled_styles'])
        style_details = self.prompt_config['styles'][style]
        
        prompt = self.strategy.generate(theme, description, style, style_details)
        print(f"\nGenerated prompt: {prompt}")
        return prompt
    
    def is_ready(self):
        """Check if the prompt generator is ready for the next prompt"""
        if isinstance(self.strategy, EnhancedPromptStrategy):
            return self.strategy.is_ready()
        return True  # Classic strategy is always ready 