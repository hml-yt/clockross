Write a clock app in Python that uses Pygame to display an analog clock. 

# Clock Face and Hands
The app will render a complete clock face with:
- A large outer circle
- Hour markers
- Hour and minute hands that are wide at the base and narrow at the tip
- A center dot

This complete clock face template will be sent as a black and white image to the Stable Diffusion API to generate a background image. The clock face will be drawn in white on a dark gray background.

# Seconds Hand
The app will then draw the seconds hand on the screen overlayed on the background image. 
The app's background should be black. The clock should be 40% transparent.
It will refresh the background image in the background every 15 seconds.

# Stable Diffusion API
The Stable Diffusion API is at http://orinputer.local:7860/sdapi/v1/txt2img.
The payload is in api_payload.json. Before calling the API, you need to encode the clock face to an image in base64 and generate a random prompt.

# Prompt
The random prompt should be similar to the prompts in prompts.txt.

# Setup
To run the app, create a setup.sh that setups a venv and installs the requirements.txt.

# Output
The app should output useful information to the console, including the prompt, when it sends the API request, and when it receives the response.

# Debug Images
The app should save debug images for:
- The clock face template being sent to the API (debug_clockface_*.png)
- The pre-API encoded image (debug_preapi_*.png)
- The generated background from the API (debug_background_*.png)