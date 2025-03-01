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
            
            # Use SmolLM2 model
            checkpoint = "HuggingFaceTB/SmolLM2-1.7B-Instruct"
            
            self.tokenizer = AutoTokenizer.from_pretrained(checkpoint)
            self.model = AutoModelForCausalLM.from_pretrained(checkpoint).to(device)
    
    def generate(self, theme, description, style, style_details):
        """Generate a prompt using the AI-enhanced strategy"""
        base_prompt = f"{style} of {theme}, {description}"
        start_time = time.time()
        
        try:
            self._initialize_model()
            enhancer_config = self.prompt_config['enhancer']
            
            # Create a message for the chat template
            messages = [{
                "role": "system", 
                "content": "You are a helpful assistant that enhances image prompts. Do not return any text other than the enhanced prompt."
            }, {
                "role": "user", 
                "content": base_prompt
            }]

            device = get_best_device()
            
            # Apply chat template
            input_text = self.tokenizer.apply_chat_template(messages, tokenize=False)
            inputs = self.tokenizer.encode(input_text, return_tensors="pt").to(device)
            
            # Generate the enhanced prompt
            outputs = self.model.generate(
                inputs,
                max_new_tokens=enhancer_config['max_length'],
                temperature=enhancer_config['temperature'],
                top_p=enhancer_config['top_p'],
                do_sample=enhancer_config['do_sample'],
            )
            
            # Decode the generated text and extract just the enhanced prompt
            enhanced_prompt = self.tokenizer.decode(outputs[0])
            
            # Find the last "Enhanced Prompt:" marker if it exists
            if "Enhanced Prompt:" in enhanced_prompt:
                enhanced_prompt = enhanced_prompt.split("Enhanced Prompt:")[-1].strip()
            # If no marker, try to get content after the last assistant message
            elif "<|im_start|>assistant" in enhanced_prompt:
                enhanced_prompt = enhanced_prompt.split("<|im_start|>assistant")[-1].strip()
            
            # Clean up any remaining markers and quotes
            enhanced_prompt = enhanced_prompt.replace("<|im_end|>", "").strip()
            enhanced_prompt = enhanced_prompt.strip('"').strip()
            
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