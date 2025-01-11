Write a clock app in Python that uses Pygame to display an analog clock. 

# Clock Hands
The clock hands shouldn't be shown on the screen, but only sent as base64 encoded images to the API.
It will render a black and white hour and minute hands, send them to a Stable Diffusion API to generate a background image.
The hands should be wide at the base and narrow at the tip.

# Seconds Hand
It will then draw the seconds hand on the screen overlayed on the background image. 
The app's background should be black. The clock should be 40% transparent.
It will refresh the background image in the background every 15 seconds.

# Stable Diffusion API
The Stable Diffusion API is at http://orinputer.local:7860/sdapi/v1/txt2img.
The payload is in api_payload.json. Before calling the API, you need to encode the hands/minutes to an image in base64 and generate a random prompt.

# Prompt
The random prompt should similar to the prompts in prompts.txt.

# Setup
To run the app, create a setup.sh that setups a venv and installs the requirements.txt. Setup a gitignore file to ignore the venv and the .DS_Store file, as well debug_*.png files.

# Output
The app should output useful information to the console, including the prompt, when it sends the API request, and when it receives the response.