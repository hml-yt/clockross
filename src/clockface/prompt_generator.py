import random
from abc import ABC, abstractmethod
from ..config import Config
from transformers import pipeline
from ..utils.device_utils import get_best_device

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
        base_prompt = f"{style} of {theme}, {description}"
        extender = self._get_prompt_extender()
        enhancer_config = self.prompt_config['enhancer']
        
        enhanced_prompt = extender(
            base_prompt,
            max_length=enhancer_config['max_length'],
            num_return_sequences=enhancer_config['num_return_sequences'],
            temperature=enhancer_config['temperature'],
            top_p=enhancer_config['top_p'],
            do_sample=enhancer_config['do_sample']
        )[0]['generated_text']
        
        return enhanced_prompt

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