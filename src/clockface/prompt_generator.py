import random
from ..config import Config

def generate_prompt():
    config = Config()
    prompt_config = config.prompts

    # Get a random theme and description
    theme = random.choice(prompt_config['themes'])
    description = random.choice(prompt_config['descriptions'])
    
    # Choose a random enabled style
    style = random.choice(prompt_config['enabled_styles'])
    style_details = prompt_config['styles'][style]
    
    # Select random details and resolutions
    selected_details = random.sample(style_details['details'], k=random.randint(2, 4))
    selected_resolutions = random.sample(prompt_config['resolutions'], k=random.randint(1, len(prompt_config['resolutions'])))
    selected_award = random.choice(style_details['awards'])
    
    return f"(\"{theme}, {description}\", \"{', '.join(selected_details)}\", \"{', '.join(selected_resolutions)}, {selected_award}\").and()"

class PromptGenerator:
    def __init__(self):
        pass
        
    def generate(self):
        """Generate a random prompt for the Stable Diffusion renderer"""
        prompt = generate_prompt()
        print(f"\nGenerated prompt: {prompt}")
        return prompt 