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

    # Style-specific details and awards
    styles = {
        "digital_art": {
            "details": [
                "ultra-detailed", "dramatic atmosphere", "vibrant and colorful", 
                "exotic and imaginative", "high-tech and sleek", "3D rendered",
                "Octane Render", "Cycles", "Blender", "3D Studio Max", "Unreal Engine", 
                "Unity", "Houdini", "Substance Painter"
            ],
            "awards": ["Trending on ArtStation", "CG Society Awards Winner"]
        },
        "renaissance": {
            "details": [
                "Italian Renaissance style", "sfumato technique", "chiaroscuro lighting",
                "oil painting texture", "classical composition", "Florentine school",
                "golden ratio composition", "masterful drapery", "religious iconography",
                "architectural perspective", "Venetian color palette", "tempera on wood"
            ],
            "awards": ["Classical Art Revival Award", "Renaissance Masters Tribute"]
        },
        "painting": {
            "details": [
                "digital painting", "digital illustration", "serene and peaceful",
                "soft and tranquil", "lush and vibrant", "nostalgic yet eerie",
                "dynamic and vivid", "dark yet beautiful"
            ],
            "awards": ["Digital Art Masters Winner", "ImagineFX Artist of the Month"]
        },
        "photo": {
            "details": [
                "hyper-realistic", "cinematic HDR lighting", "shot on Sony A7R IV",
                "Zeiss 55mm f1.4", "shot on Canon EOS R5", "shot on Nikon Z9",
                "shot on Fujifilm X-T4"
            ],
            "awards": ["Sony World Photography Awards Winner", "National Geographic Photo of the Day"]
        },
        "anime": {
            "details": [
                "anime style", "manga art", "cel shaded", "Studio Ghibli inspired",
                "J-animation", "kawaii aesthetic", "anime lighting",
                "sharp line art", "vibrant anime colors"
            ],
            "awards": ["Anime & Manga Awards Winner", "Japan Media Arts Festival Selection"]
        },
        "concept_art": {
            "details": [
                "professional concept art", "entertainment design", "key art",
                "production design", "environmental concept", "character design",
                "industry standard", "cinematic composition"
            ],
            "awards": ["Spectrum Fantasy Art Award", "Industry Choice Award"]
        },
        "pixel_art": {
            "details": [
                "16-bit style", "32-bit style", "retro gaming aesthetic",
                "pixel perfect", "limited palette", "dithering",
                "sprite art style", "isometric pixel art"
            ],
            "awards": ["Pixel Art Festival Winner", "Retro Gaming Art Award"]
        },
        "watercolor": {
            "details": [
                "watercolor technique", "wet on wet", "flowing colors",
                "traditional media simulation", "organic textures",
                "soft color bleeding", "painterly style"
            ],
            "awards": ["Traditional Media Excellence", "Watercolor Society Selection"]
        },
        "minimalist": {
            "details": [
                "clean design", "minimal composition", "geometric shapes",
                "limited color palette", "negative space", "modern simplicity",
                "elegant minimalism"
            ],
            "awards": ["Modern Design Award", "Minimalist Art Selection"]
        }
    }

    resolutions = ["8k", "16k", "32k", "HDR"]
    
    # Choose a random style
    style = random.choice(list(styles.keys()))
    style_details = styles[style]
    
    theme = random.choice(themes)
    description = random.choice(descriptions)
    selected_details = random.sample(style_details["details"], k=random.randint(2, 4))
    selected_resolutions = random.sample(resolutions, k=random.randint(1, len(resolutions)))
    selected_award = random.choice(style_details["awards"])
    
    return f"(\"{theme}, {description}\", \"{', '.join(selected_details)}\", \"{', '.join(selected_resolutions)}, {selected_award}\").and()"

class PromptGenerator:
    def __init__(self):
        pass
        
    def generate(self):
        """Generate a random prompt for the Stable Diffusion renderer"""
        prompt = generate_prompt()
        print(f"\nGenerated prompt: {prompt}")
        return prompt 