import random

def generate_prompt():
    # Define lists of options for each segment of the prompt
    themes = [
        "a tranquil Japanese zen garden", "a futuristic neon cityscape", "a surreal dreamscape",
        "a vast desert", "an icy tundra", "a lush rainforest", "a magical underwater world",
        "a bustling medieval marketplace", "a volcanic landscape", "a steampunk cityscape",
        "an enchanted forest", "a celestial space scene", "a post-apocalyptic wasteland",
        "a vibrant alien planet", "a mystical ancient forest", "a massive underground cavern",
        "a sprawling futuristic space station", "an abandoned theme park", "a serene alpine lake",
        "a dense fog-covered marshland", "a grand futuristic library", "a post-apocalyptic cityscape",
        "a tropical rainforest", "a peaceful icy archipelago"
    ]

    descriptions = [
        "at sunrise", "at sunset", "under the aurora borealis", "at twilight",
        "during a thunderstorm", "under a golden sky", "with glowing bioluminescent plants",
        "with cascading waterfalls", "with intricate carvings", "with overgrown ruins",
        "with futuristic technology", "with shafts of sunlight piercing through",
        "with vibrant coral reefs", "with swirling nebulae in the sky", "with ancient trees",
        "with soft mist rolling through", "with dynamic lighting", "under a sky filled with stars",
        "with glowing mushrooms", "with floating islands", "over a frozen ocean", "with towering shelves of glowing books"
    ]

    details = [
        "ultra-detailed", "hyper-realistic", "cinematic HDR lighting", "dramatic atmosphere", 
        "serene and peaceful", "eerie and haunting", "vibrant and colorful", "exotic and imaginative", 
        "dark yet beautiful", "nostalgic yet eerie", "dynamic and vivid", "soft and tranquil", 
        "high-tech and sleek", "lush and vibrant", "ancient and mysterious"
    ]

    resolutions = ["8k", "16k", "32k", "HDR"]

    theme = random.choice(themes)
    description = random.choice(descriptions)
    selected_details = random.sample(details, k=random.randint(2, 4))  # Choose 2 to 4 details
    selected_resolutions = random.sample(resolutions, k=random.randint(1, len(resolutions)))  # Choose 1 to all resolutions
    return f"{theme}, {description}, {', '.join(selected_details)}, {', '.join(selected_resolutions)}, trending on ArtStation"

class PromptGenerator:
    def __init__(self):
        pass
        
    def generate(self):
        """Generate a random prompt for the Stable Diffusion renderer"""
        prompt = generate_prompt()
        print(f"\nGenerated prompt: {prompt}")
        return prompt 