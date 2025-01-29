# ClockRoss - AI-Powered Analog Clock

An elegant analog clock application that uses local Stable Diffusion (via Diffusers) with ControlNet to generate dynamic, artistic backgrounds. The clock features a clean, modern design with smooth animations and semi-transparent overlays that adapt to the generated background. Prompts are enhanced using GPT-2 for more creative and coherent results.

## Features

- Real-time analog clock with customizable movement styles
- Local AI background generation using Hugging Face Diffusers with ControlNet
- GPT-2 enhanced prompt generation system
- 20-second background refresh interval
- Smooth animations and transitions
- High-resolution display (1024x600) with optimized generation resolution (640x360)
- Comprehensive debug mode for development
- Dual configuration system (global and local)
- Multiple clock face and movement styles
- Support for both CUDA (NVIDIA) and MPS (Apple Silicon) acceleration
- Flexible display modes (fullscreen or windowed)

## Project Structure

```
.
├── src/
│   ├── clockface/           # Clock face rendering and management
│   │   ├── surface_manager.py
│   │   ├── prompt_generator.py
│   │   ├── diffusion_pipeline.py
│   │   └── background_updater.py
│   ├── movement/            # Clock movement and animations
│   │   └── clock_face.py
│   ├── settings/           # Application settings
│   ├── utils/             # Utility functions
│   ├── config.py          # Core configuration
│   └── __init__.py
├── main.py                # Application entry point
├── config.yaml           # Global configuration file
├── local_config.yaml     # Local overrides and sensitive settings
├── setup-clockross.sh    # Setup script
├── requirements.txt      # Python dependencies
└── README.md
```

## Requirements

- Python 3.8 or higher
- One of:
  - CUDA-capable GPU (NVIDIA, recommended)
  - Apple Silicon processor (M1 or newer)
- Dependencies listed in requirements.txt
- Minimum requirements:
  - NVIDIA: 8GB GPU VRAM
  - Apple Silicon: 16GB unified memory recommended

## Installation

1. Clone the repository
2. Run the setup script:
   ```bash
   ./setup-clockross.sh
   ```
   This will:
   - Create a virtual environment
   - Install dependencies
   - Configure initial settings
   - Download required models (Stable Diffusion, ControlNet, GPT-2)
   - Create a template local_config.yaml
   - Detect and configure appropriate acceleration (CUDA/MPS)

Note: For Jetson Orin Nano devices, use the setup script above for standard installation.

## Development Setup

For development purposes, follow these steps instead:

1. Create a Python 3.10 virtual environment:
   ```bash
   python3.10 -m venv venv
   ```

2. Activate the virtual environment:
   ```bash
   # On Unix/macOS
   source venv/bin/activate
   # On Windows
   .\venv\Scripts\activate
   ```

3. Install dependencies and run the application:
   ```bash
   pip install -r requirements.txt
   python main.py [options]
   ```

## Usage

Run the application:
```bash
python main.py [options]
```

Options:
- `--debug`: Enable debug mode (saves debug images and shows verbose output)
- `--windowed`: Run in windowed mode instead of fullscreen

The application automatically selects the best available hardware acceleration:
- CUDA on systems with NVIDIA GPUs
- MPS on Apple Silicon devices
- CPU as fallback when no acceleration is available

## Configuration

The application uses a dual configuration system:

### Global Configuration (config.yaml)
- Display settings (resolution, transparency)
- Model parameters and pipeline settings
- ControlNet configuration
- GPT-2 prompt generation and enhancement settings
- Clock face styles and movement patterns
- Background update intervals (20s default)
- Debug settings
- Hardware acceleration settings (CUDA/MPS)
- Display mode preferences

### Local Configuration (local_config.yaml)
- Machine-specific overrides
- Local model paths and cache settings
- Custom generation parameters
- ControlNet and GPT-2 model paths
- Development settings
- Personal preferences
- Device-specific optimizations
- Display preferences

Note: `local_config.yaml` is gitignored and should not be committed to version control.

## Debug Mode

When running with `--debug`, the following debug files are generated in the `debug/` directory:

- `debug_prerender_*.png`: Clock face pre-rendering
- `debug_control_*.png`: ControlNet conditioning images
- `debug_background_*.png`: Generated backgrounds
- `debug_composite_*.png`: Final composite views
- `debug_prompts.log`: Raw and enhanced prompt pairs

Debug mode also provides detailed logging about:
- Generation pipeline operations
- ControlNet conditioning
- GPT-2 prompt enhancement
- Background generation
- Performance metrics
- Movement calculations
- Model loading and memory usage

## Hardware Acceleration

The application supports multiple acceleration backends:

### NVIDIA GPUs (CUDA)
- Recommended for Windows and Linux
- Requires CUDA-capable GPU
- Minimum 8GB VRAM recommended

### Apple Silicon (MPS)
- Native support for M1 and newer Apple processors
- Leverages Metal Performance Shaders
- Optimized for unified memory architecture
- Recommended 16GB unified memory

### CPU Fallback
- Available when no GPU acceleration is present
- Significantly slower performance
- Not recommended for regular use

## Resolution Management

The application uses two resolution modes:
- Display: 1024x600 (window size)
- Generation: 640x360 (Stable Diffusion input/output)

This optimizes for:
- GPU memory usage
- Generation speed
- System resources
- Display quality

## Models

The application uses three main AI models:
1. Stable Diffusion (default: revAnimated) - Background generation
2. ControlNet - Composition control and guidance
3. GPT-2 - Prompt enhancement and refinement

## License

MIT License 