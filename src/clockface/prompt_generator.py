import random
from abc import ABC, abstractmethod

import torch
from ..config import Config
from transformers import AutoModelForCausalLM, AutoTokenizer
from ..utils.device_utils import get_best_device
import time

class PromptStrategy(ABC):
    """Abstract base class for prompt generation strategies"""
    def __init__(self, config):
        self.config = config
        self.prompt_config = config.prompts

    @abstractmethod
    def generate(self, theme, description, style, style_details):
        """Generate a prompt using the specific strategy
        Returns:
            tuple: (prompt, enhancement_time)
        """
        pass

class ClassicPromptStrategy(PromptStrategy):
    """Classic prompt generation strategy using random selection and combination"""
    def generate(self, theme, description, style, style_details):
        selected_details = random.sample(style_details['details'], k=random.randint(2, 4))
        selected_resolutions = random.sample(self.prompt_config['resolutions'], k=random.randint(1, len(self.prompt_config['resolutions'])))
        selected_award = random.choice(style_details['awards'])
        
        prompt = f"{theme}, {description}, {', '.join(selected_details)}, {', '.join(selected_resolutions)}, {selected_award}"
        return prompt, 0.0  # No enhancement time for classic strategy

class EnhancedPromptStrategy(PromptStrategy):
    """AI-enhanced prompt generation strategy using language model"""
    def __init__(self, config):
        super().__init__(config)
        self.model = None
        self.tokenizer = None
    
    def _initialize_model(self):
        if self.model is None or self.tokenizer is None:
            enhancer_config = self.prompt_config['enhancer']
            device = get_best_device()
            
            if device == "cuda":
                model_kwargs = {
                    "attn_implementation": "flash_attention_2",
                    "torch_dtype": torch.float16,
                    "device_map": "auto",
                    "use_cache": True,
                }
            else:
                model_kwargs = {}
            
            self.model = AutoModelForCausalLM.from_pretrained(
                enhancer_config['model'],
                **model_kwargs
            )
            self.tokenizer = AutoTokenizer.from_pretrained(enhancer_config['model'])
            
            if device == "cuda":
                self.model = self.model.to(device)
    
    def generate(self, theme, description, style, style_details):
        """Generate a prompt using the AI-enhanced strategy"""
        base_prompt = f"{style} of {theme}, {description}"
        start_time = time.time()
        
        try:
            self._initialize_model()
            enhancer_config = self.prompt_config['enhancer']
            
            inputs = self.tokenizer(base_prompt, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            gen_tokens = self.model.generate(
                **inputs,
                max_length=enhancer_config['max_length'],
                max_time=enhancer_config['max_time'],
                num_return_sequences=enhancer_config['num_return_sequences'],
                temperature=enhancer_config['temperature'],
                top_p=enhancer_config['top_p'],
                do_sample=enhancer_config['do_sample'],
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            enhanced_prompt = self.tokenizer.batch_decode(gen_tokens, skip_special_tokens=True)[0]
            
            enhancement_time = time.time() - start_time
            print(f"Prompt enhancement took {enhancement_time:.2f}s")
            
            return enhanced_prompt, enhancement_time
        except Exception as e:
            print(f"Error enhancing prompt: {e}")
            return base_prompt, 0.0
    
    def is_ready(self):
        """Check if the prompt generator is ready (not currently enhancing a prompt)"""
        return True  # Always ready since we're not using queues anymore

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
        
        prompt, enhancement_time = self.strategy.generate(theme, description, style, style_details)
        print(f"\nGenerated prompt: {prompt}")
        return prompt, enhancement_time
    
    def is_ready(self):
        """Check if the prompt generator is ready for the next prompt"""
        if isinstance(self.strategy, EnhancedPromptStrategy):
            return self.strategy.is_ready()
        return True  # Classic strategy is always ready 