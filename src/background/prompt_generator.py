import random

class PromptGenerator:
    def __init__(self):
        # Time and lighting
        self.times = [
            "at dawn", "at dusk", "under moonlight", "in twilight", "at midnight",
            "during golden hour", "under a blood moon", "during solar eclipse",
            "in perpetual twilight", "under starlight", "at sunrise", "at sunset"
        ]
        
        # Environments and landscapes
        self.environments = [
            "in a crystalline cave", "in an ancient temple", "in a floating city",
            "in a submerged cathedral", "in a cosmic void", "in a quantum realm",
            "in a steampunk workshop", "in a celestial observatory",
            "in a forgotten library", "in an enchanted forest", "in a desert oasis",
            "in a volcanic sanctuary", "in an arctic cathedral", "in a cloud kingdom",
            "in a bioluminescent grove", "in a crystal canyon", "in a meteor crater",
            "in a temporal nexus", "in an astral plane", "in a dimensional rift"
        ]
        
        # Main subjects and focal points
        self.main_elements = [
            "a grand clockwork mechanism", "an ancient timekeeper's sanctuary",
            "a cosmic observatory", "a temporal dimension", "a time-bending realm",
            "a celestial chronometer", "an ethereal timescape", "a time wizard's study",
            "a chronograph temple", "a temporal engine", "a reality-warping device",
            "an interdimensional timepiece", "a cosmic time portal", "a quantum clock tower",
            "an astrolabe sanctuary", "a temporal compass", "a time crystal formation",
            "a mechanical constellation", "a dimensional sundial", "an ethereal hourglass"
        ]
        
        # Atmospheric elements and details
        self.details = [
            "intricate gears floating in space", "swirling time spirals",
            "floating numerical constellations", "temporal energy streams",
            "crystalline chronographs", "orbiting time fragments",
            "cascading light particles", "flowing time rivers", "dancing auroras",
            "geometric light patterns", "holographic time glyphs", "levitating crystals",
            "temporal storm clouds", "quantum dust motes", "prismatic refractions",
            "nebulous time streams", "fractal patterns", "cosmic clockwork",
            "temporal butterflies", "chronometric fractals", "time-worn artifacts",
            "ethereal wisps", "dimensional echoes", "crystalline formations",
            "ancient runes", "floating mathematical equations", "astral projections"
        ]
        
        # Mood and atmosphere
        self.atmospheres = [
            "serene and mysterious", "enigmatic and profound",
            "timeless and ethereal", "cosmic and surreal",
            "mystical and ancient", "otherworldly and transcendent",
            "dreamlike and floating", "metaphysical and abstract",
            "sacred and divine", "infinite and vast", "peaceful and harmonious",
            "magical and enchanted", "celestial and cosmic", "ethereal and ghostly"
        ]
        
        # Technical qualities
        self.qualities = [
            "ultra-detailed", "hyper-realistic", "HDR", "8k", "32k",
            "cinematic lighting", "dramatic atmosphere", "volumetric lighting",
            "ray tracing", "photorealistic", "studio quality", "professional photography",
            "octane render", "unreal engine", "dynamic range", "atmospheric perspective"
        ]
        
        # Story elements
        self.stories = [
            "where time stands still", "where past meets future",
            "where reality bends", "where dimensions converge",
            "where time flows backwards", "where eternity unfolds",
            "where moments crystallize", "where infinity loops",
            "where chronology fractures", "where time spirals endlessly"
        ]

    def generate(self):
        """Generate a random prompt for the Stable Diffusion API"""
        prompt_structures = [
            # Structure 1: Environment-focused
            f"A {random.choice(self.environments)} {random.choice(self.times)}, featuring {random.choice(self.main_elements)}, {random.choice(self.details)}, {random.choice(self.details)}, {random.choice(self.stories)}, {random.choice(self.atmospheres)}, {random.choice(self.qualities)}, {random.choice(self.qualities)}",
            
            # Structure 2: Main element-focused
            f"{random.choice(self.main_elements)} {random.choice(self.times)} {random.choice(self.environments)}, {random.choice(self.details)}, {random.choice(self.stories)}, {random.choice(self.atmospheres)}, {random.choice(self.qualities)}, {random.choice(self.qualities)}",
            
            # Structure 3: Story-focused
            f"A realm {random.choice(self.stories)}, {random.choice(self.environments)}, with {random.choice(self.main_elements)}, {random.choice(self.details)}, {random.choice(self.atmospheres)}, {random.choice(self.qualities)}, {random.choice(self.qualities)}"
        ]
        
        prompt = f"{random.choice(prompt_structures)}, trending on ArtStation"
        print(f"\nGenerated prompt: {prompt}")
        return prompt 