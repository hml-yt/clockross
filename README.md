# AI-Powered Analog Clock

An elegant analog clock application that uses Stable Diffusion AI to generate dynamic, artistic backgrounds that change every 15 seconds. The clock features a clean, modern design with smooth animations and semi-transparent overlays that adapt to the generated background.

## Features

- Real-time analog clock with hour, minute, and second hands
- AI-generated backgrounds using Stable Diffusion
- Dynamic color adaptation based on the generated background
- Smooth animations and transitions
- High-resolution display (1024x600) with optimized API rendering (640x360)
- Debug mode for development and troubleshooting

## Project Structure

```
.
├── src/
│   ├── clock/
│   │   ├── __init__.py
│   │   └── clock_face.py
│   ├── background/
│   │   ├── __init__.py
│   │   ├── background_updater.py
│   │   └── prompt_generator.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── image_utils.py
│   └── __init__.py
├── main.py
├── api_payload.json
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.8 or higher
- Stable Diffusion API endpoint
- Dependencies listed in requirements.txt

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your Stable Diffusion API endpoint in main.py
5. Ensure api_payload.json is properly configured for your Stable Diffusion setup

## Usage

Run the application:
```bash
python main.py [--debug]
```

Options:
- `--debug`: Enable debug mode to save debug images and show verbose output

The clock will start and automatically generate new backgrounds every 15 seconds.

## Configuration

- The Stable Diffusion API endpoint can be configured in main.py
- Display resolution (1024x600) and API resolution (640x360) can be adjusted in main.py
- Background update interval (15 seconds) can be modified in main.py
- Prompt generation parameters can be modified in src/background/prompt_generator.py

## Resolution Settings

The application uses two different resolutions:
- Display Resolution: 1024x600 - The actual window size and final rendering resolution
- API Resolution: 640x360 - The resolution used for Stable Diffusion API requests

This dual-resolution approach provides several benefits:
1. Faster API processing with smaller images
2. Reduced bandwidth usage
3. Better performance on lower-end systems
4. High-quality display output through proper scaling

## Development

When running with the `--debug` flag, debug images are automatically saved during runtime:
- Pre-API clock face images: debug_preapi_*.png (640x360)
- Generated backgrounds: debug_background_*.png (640x360)
- Clock face overlays: debug_clockface_*.png (1024x600)

The debug mode also provides verbose output about:
- API requests and responses
- Background update timing
- Color extraction results

## License

MIT License 