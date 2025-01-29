# ClockRoss - AI-Powered Analog Clock

A Python-based analog clock application that combines real-time clock display with AI-generated backgrounds using local Stable Diffusion via Diffusers, enhanced with ControlNet and GPT-2 prompt generation. Supports both NVIDIA (CUDA) and Apple Silicon (MPS) hardware acceleration.

## Core Components

### Clock Face and Movement
- Renders a complete analog clock face with:
  - Customizable outer circle and design elements
  - Hour markers and numerals
  - Hour, minute, and second hands with dynamic styling
  - Center decoration and additional design elements
- Clock elements are rendered in white on a transparent background
- Supports multiple movement styles and animations

### Background Generation
- Uses local Stable Diffusion via Diffusers library with ControlNet integration
- Clock face template is used as a ControlNet conditioning image
- Backgrounds refresh automatically every 20 seconds
- Supports multiple Stable Diffusion models with "revAnimated" as default
- AI-enhanced prompt generation using GPT-2
- Advanced composition control through ControlNet guidance

### Display System
- Main display resolution: 1024x600
- Generation resolution: 640x360
- Semi-transparent clock overlay (40%)
- Smooth animations and transitions
- Dynamic color adaptation
- Supports both fullscreen and windowed modes
- Automatic display scaling and positioning

### Hardware Acceleration
- Multi-platform acceleration support:
  - NVIDIA GPUs via CUDA
  - Apple Silicon via Metal Performance Shaders (MPS)
  - CPU fallback for compatibility
- Automatic device detection and configuration
- Optimized memory management for each platform
- Dynamic batch size adjustment based on available memory

## Technical Implementation

### Diffusion Pipeline
- Local image generation using Hugging Face Diffusers
- ControlNet integration for precise background control
- Platform-specific optimizations (CUDA/MPS)
- Configurable pipeline parameters via config.yaml
- Memory-optimized inference with model offloading
- Advanced composition control via ControlNet conditioning

### Prompt Generation
- Multi-stage prompt generation system:
  - Base prompt template selection
  - GPT-2 enhancement and expansion
  - Style and theme integration
  - Technical parameter adjustment
- AI-driven prompt refinement
- Customizable enhancement templates
- Consistent style maintenance across generations

### Debug Features
Debug mode (--debug flag) generates:
- Pre-render clock face images (debug_prerender_*.png)
- ControlNet conditioning images (debug_control_*.png)
- Generated backgrounds (debug_background_*.png)
- Composite debug views (debug_composite_*.png)
- Raw and enhanced prompts (debug_prompts.log)
- Performance metrics for different devices

### Project Structure
```
src/
├── clockface/          # Clock face rendering and management
├── movement/           # Clock hand movement and animations
├── settings/          # Application settings and configuration
├── utils/            # Utility functions and helpers
└── config.py         # Core configuration
```

## Setup and Configuration
- Automated setup script (setup-clockross.sh)
- Python virtual environment management
- Dependency installation via requirements.txt
- Dual configuration system:
  - Global settings via config.yaml
  - Local overrides via local_config.yaml (gitignored)
- Automatic model downloading and caching
- Hardware acceleration detection and setup
- Display mode configuration

## Configuration Files

### Global Configuration (config.yaml)
- Core application settings
- Default model parameters
- ControlNet settings
- GPT-2 configuration
- Display and animation settings
- Hardware acceleration preferences
- Window mode settings
- Debug configuration
- Default prompt templates

### Local Configuration (local_config.yaml)
- Machine-specific settings
- Local model paths (Stable Diffusion, ControlNet, GPT-2)
- Cache directory locations
- Development overrides
- Personal customizations
- Model-specific parameters
- Device-specific optimizations
- Display preferences

## Command Line Options
- --debug: Enable debug mode
- --windowed: Run in windowed mode

Hardware acceleration is automatically selected based on the available hardware:
- NVIDIA GPUs: CUDA acceleration
- Apple Silicon: MPS acceleration
- Other systems: CPU fallback

## Logging and Monitoring
The application provides detailed logging:
- Raw and enhanced prompt details
- Generation pipeline timing
- Background update status (20-second intervals)
- Performance metrics
- Debug image generation status
- Model loading and memory usage
- ControlNet conditioning status
- GPT-2 prompt enhancement details