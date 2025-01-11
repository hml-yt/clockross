# AI-Powered Analog Clock

An elegant analog clock application that uses Stable Diffusion AI to generate dynamic, artistic backgrounds that change every 15 seconds. The clock features a clean, modern design with smooth animations and semi-transparent overlays that adapt to the generated background.

## Features

- Real-time analog clock with hour, minute, and second hands
- AI-generated backgrounds using Stable Diffusion
- Dynamic color adaptation based on the generated background
- Smooth animations and transitions
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
- Clock dimensions and update intervals can be adjusted in main.py
- Prompt generation parameters can be modified in src/background/prompt_generator.py

## Development

When running with the `--debug` flag, debug images are automatically saved during runtime:
- Pre-API clock face images: debug_preapi_*.png
- Generated backgrounds: debug_background_*.png
- Clock face overlays: debug_clockface_*.png

The debug mode also provides verbose output about:
- API requests and responses
- Background update timing
- Color extraction results

## License

MIT License 