import pygame
import pygame.gfxdraw
import random
import os
import json
from datetime import datetime
from ..config import Config
import time
import requests

class Dialog:
    def __init__(self, screen_width, screen_height, font):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = font
        self.padding = 30
        self.visible = False
        self.start_time = 0
        self.duration = None  # None for confirmation dialogs, seconds for notifications
        self.buttons = []  # Empty for notifications
        self.message = ""
        self.title = ""
        self.callback = None
        
    def show_confirmation(self, title, message, callback):
        """Show a confirmation dialog with Yes/No buttons"""
        self.title = title
        self.message = message
        self.callback = callback
        self.duration = None
        self.buttons = ["Yes", "No"]
        self.visible = True
        
    def show_notification(self, message, duration=2):
        """Show a temporary notification message"""
        self.title = ""
        self.message = message
        self.callback = None
        self.duration = duration
        self.buttons = []
        self.visible = True
        self.start_time = time.time()
        
    def handle_click(self, pos):
        """Handle click events for the dialog"""
        if not self.visible or not self.buttons:
            return False
            
        dialog_width = 400
        dialog_height = 200
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        # Check if click is outside dialog
        if not (dialog_x <= pos[0] <= dialog_x + dialog_width and
                dialog_y <= pos[1] <= dialog_y + dialog_height):
            self.visible = False
            return True
            
        # Handle button clicks for confirmation dialog
        button_width = (dialog_width - 3 * self.padding) // 2
        button_height = 60
        button_y = dialog_height - self.padding - button_height
        
        # Check Yes button
        yes_rect = pygame.Rect(
            dialog_x + self.padding,
            dialog_y + button_y,
            button_width,
            button_height
        )
        if yes_rect.collidepoint(pos[0], pos[1]):
            if self.callback:
                self.callback(True)
            self.visible = False
            return True
        
        # Check No button
        no_rect = pygame.Rect(
            dialog_x + dialog_width - self.padding - button_width,
            dialog_y + button_y,
            button_width,
            button_height
        )
        if no_rect.collidepoint(pos[0], pos[1]):
            if self.callback:
                self.callback(False)
            self.visible = False
            return True
        
        return True
        
    def draw(self, surface):
        """Draw the dialog"""
        if not self.visible:
            return
            
        # Handle auto-hide for notifications
        if self.duration is not None:
            current_time = time.time()
            if current_time - self.start_time > self.duration:
                self.visible = False
                return
                
        # For notifications, use a smaller dialog
        if not self.buttons:
            # Calculate fade out alpha for notifications
            alpha = 255
            if self.duration is not None:
                alpha = int(255 * (1 - (time.time() - self.start_time) / self.duration))
            
            # Draw notification with wider width
            message_surface = pygame.Surface((500, 60), pygame.SRCALPHA)
            message_text = self.font.render(self.message, True, (255, 255, 255))
            text_rect = message_text.get_rect(center=(250, 30))
            
            # Draw semi-transparent background
            pygame.draw.rect(message_surface, (40, 40, 40, min(200, alpha)), message_surface.get_rect(), border_radius=10)
            pygame.draw.rect(message_surface, (80, 80, 80, min(200, alpha)), message_surface.get_rect(), 2, border_radius=10)
            
            # Apply fade out to text
            message_text.set_alpha(alpha)
            message_surface.blit(message_text, text_rect)
            
            # Position at bottom center of screen
            message_x = (self.screen_width - 500) // 2
            message_y = self.screen_height - 80
            surface.blit(message_surface, (message_x, message_y))
            return
            
        # Draw darkened overlay for confirmation dialogs
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        surface.blit(overlay, (0, 0))
        
        # Draw confirmation dialog
        dialog_width = 400
        dialog_height = 200
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        dialog_surface = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
        pygame.draw.rect(dialog_surface, (40, 40, 40, 250), dialog_surface.get_rect())
        pygame.draw.rect(dialog_surface, (80, 80, 80), dialog_surface.get_rect(), 2)
        
        # Draw title
        title = self.font.render(self.title, True, (255, 255, 255))
        title_x = (dialog_width - title.get_width()) // 2
        dialog_surface.blit(title, (title_x, self.padding))
        
        # Draw message
        message = self.font.render(self.message, True, (255, 255, 255))
        message_x = (dialog_width - message.get_width()) // 2
        dialog_surface.blit(message, (message_x, self.padding + 45))
        
        # Draw buttons
        button_width = (dialog_width - 3 * self.padding) // 2
        button_height = 60
        button_y = dialog_height - self.padding - button_height
        
        # Yes button (red)
        yes_rect = pygame.Rect(self.padding, button_y, button_width, button_height)
        pygame.draw.rect(dialog_surface, (180, 60, 60), yes_rect)
        pygame.draw.rect(dialog_surface, (200, 80, 80), yes_rect, 2)
        yes_text = self.font.render("Yes", True, (255, 255, 255))
        text_x = self.padding + (button_width - yes_text.get_width()) // 2
        dialog_surface.blit(yes_text, (text_x, button_y + (button_height - yes_text.get_height()) // 2))
        
        # No button (blue)
        no_rect = pygame.Rect(dialog_width - self.padding - button_width, button_y, button_width, button_height)
        pygame.draw.rect(dialog_surface, (60, 120, 180), no_rect)
        pygame.draw.rect(dialog_surface, (80, 140, 200), no_rect, 2)
        no_text = self.font.render("No", True, (255, 255, 255))
        text_x = dialog_width - self.padding - button_width + (button_width - no_text.get_width()) // 2
        dialog_surface.blit(no_text, (text_x, button_y + (button_height - no_text.get_height()) // 2))
        
        surface.blit(dialog_surface, (dialog_x, dialog_y))

class SettingsUI:
    def __init__(self, screen_width, screen_height, background_updater=None, surface_manager=None):
        self.config = Config()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        self.background_updater = background_updater
        self.surface_manager = surface_manager
        self.checkpoint_changed = False
        self.notification = None
        self.notification_start = 0
        self.notification_duration = None
        
        # UI settings
        self.padding = 30
        self.item_height = 60
        self.font_size = 32
        self.font = pygame.font.Font(None, self.font_size)
        self.panel_width = 600
        
        # Dialog system
        self.dialog = Dialog(screen_width, screen_height, self.font)
        self.dialog.settings_ui = self
        
        # Colors
        self.panel_color = (30, 30, 30, 220)
        self.text_color = (255, 255, 255)
        self.active_color = (0, 120, 255)
        
        # Font options for random selection
        self.font_options = ["Arial", "Helvetica", "Times New Roman", "Brush Script MT"]
        
        # Get available models
        self.available_models = self._get_available_models()

        # Define contrast levels
        self.contrast_levels = {
            'High': [30, 30, 30],
            'Medium': [60, 60, 60],
            'Low': [90, 90, 90]
        }
        
        # Define settings
        self.settings = [
            {
                'name': 'Display Mode',
                'key': ('clock', 'display_mode'),
                'type': 'select',
                'value': self.config.clock['display_mode'],
                'options': ['screen_only', 'render_only', 'both']
            },
            {
                'name': 'Use Numbers',
                'key': ('clock', 'use_numbers'),
                'type': 'bool',
                'value': self.config.clock['use_numbers']
            },
            {
                'name': 'Contrast',
                'key': ('render', 'background_color'),
                'type': 'select',
                'value': 'Medium',  # Default to medium
                'options': list(self.contrast_levels.keys())
            },
            {
                'name': 'Model Checkpoint',
                'key': ('render', 'checkpoint'),
                'type': 'dropdown',
                'label': 'Model',
                'description': 'Stable Diffusion model to use',
                'value': self.config.render['checkpoint'],
                'options': self.available_models
            },
            {
                'name': 'Save snapshot',
                'type': 'action',
                'action': 'snapshot'
            },
            {
                'name': 'System',
                'type': 'system_row',
                'options': ['Shutdown', 'Restart']
            }
        ]
        
        # Calculate panel dimensions
        self.panel_height = len(self.settings) * self.item_height + 2 * self.padding
        self.panel_x = (screen_width - self.panel_width) // 2
        self.panel_y = (screen_height - self.panel_height) // 2

    def handle_shutdown(self, confirmed):
        """Handle shutdown confirmation"""
        if confirmed:
            os.system(self.config.system['shutdown_cmd'])

    def handle_restart(self, confirmed):
        """Handle restart confirmation"""
        if confirmed:
            os.system(self.config.system['restart_cmd'])

    def show_notification(self, message, duration=2):
        """Show a notification message"""
        self.notification = message
        self.notification_duration = duration
        self.notification_start = time.time()

    def toggle(self):
        """Toggle settings visibility"""
        if self.visible:  # If we're closing the panel
            self.visible = False  # Hide dialog first
            if self.checkpoint_changed and self.background_updater:
                # Show notifications after a slight delay to ensure settings is hidden
                pygame.time.wait(100)  # Short delay
                self.show_notification(f"Loading checkpoint: {self.config.render['checkpoint'].split('_')[0]}...", duration=30)  # Long duration
                def on_pipeline_loaded():
                    self.show_notification("New checkpoint loaded", duration=2)
                    self.background_updater.last_attempt = 0  # Force update after loading
                self.background_updater.reload_pipeline(complete_callback=on_pipeline_loaded)  # Reload with callback
                self.checkpoint_changed = False
            return
        self.visible = True
    
    def handle_click(self, pos):
        """Handle click events in the settings UI"""
        # Check if dialog is visible and handle its clicks first
        if self.dialog.visible:
            return self.dialog.handle_click(pos)
            
        # Get panel bounds
        panel_x = (self.screen_width - self.panel_width) // 2
        panel_y = (self.screen_height - self.panel_height) // 2
        
        # If settings is visible and click is inside panel, handle settings interactions
        if self.visible and (panel_x <= pos[0] <= panel_x + self.panel_width and
                panel_y <= pos[1] <= panel_y + self.panel_height):
            # Handle setting changes
            for i, setting in enumerate(self.settings):
                item_y = panel_y + self.padding + i * self.item_height
                item_rect = pygame.Rect(panel_x + self.padding, item_y, self.panel_width - 2 * self.padding, self.item_height)
                
                if item_rect.collidepoint(pos[0], pos[1]):
                    if setting['type'] == 'select' or setting['type'] == 'dropdown':
                        current_value = setting['value']
                        current_index = setting['options'].index(current_value)
                        next_index = (current_index + 1) % len(setting['options'])
                        setting['value'] = setting['options'][next_index]
                        
                        # Update config
                        section, key = setting['key']
                        if key == 'background_color':
                            # Convert contrast level to RGB
                            rgb_value = self.contrast_levels[setting['value']]
                            self.config.update(section, key, rgb_value)
                        else:
                            self.config.update(section, key, setting['value'])
                        
                        # Special handling for checkpoint change
                        if section == 'render' and key == 'checkpoint':
                            self.checkpoint_changed = True
                        
                    elif setting['type'] == 'bool':
                        setting['value'] = not setting['value']
                        section, key = setting['key']
                        self.config.update(section, key, setting['value'])
                        
                    elif setting['type'] == 'action' and setting['action'] == 'snapshot':
                        self.visible = False
                        self.show_notification("Saving snapshot...", duration=2)
                        self.take_screenshot()
                        
                    elif setting['type'] == 'system_row':
                        option_width = (self.panel_width - 3 * self.padding) // 2
                        shutdown_rect = pygame.Rect(panel_x + self.padding, item_y, option_width, self.item_height)
                        restart_rect = pygame.Rect(panel_x + self.panel_width - self.padding - option_width, item_y, option_width, self.item_height)
                        
                        if shutdown_rect.collidepoint(pos[0], pos[1]):
                            self.dialog.show_confirmation("Shutdown", "Are you sure you want to shutdown?", self.handle_shutdown)
                        elif restart_rect.collidepoint(pos[0], pos[1]):
                            self.dialog.show_confirmation("Restart", "Are you sure you want to restart?", self.handle_restart)
                    
                    return True
        else:
            # Any click outside when visible, or any click when not visible, toggles visibility
            self.toggle()
            return True
        
        return True

    def take_screenshot(self):
        """Take screenshots of the clock face, hands, and save render request"""
        if not self.surface_manager:
            return
        self.surface_manager.save_snapshot()

    def draw(self, surface):
        """Draw the settings UI if visible"""
        if self.visible:
            # Draw settings panel
            panel_surface = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
            pygame.draw.rect(panel_surface, self.panel_color, panel_surface.get_rect())
            
            # Draw settings items
            for i, setting in enumerate(self.settings):
                item_rect = pygame.Rect(
                    0,
                    self.padding + i * self.item_height,
                    self.panel_width,
                    self.item_height
                )
                
                if setting['type'] == 'system_row':
                    # Draw system row with two buttons
                    button_width = (self.panel_width - 3 * self.padding) // 2
                    button_height = self.item_height - 10
                    button_y = self.padding + i * self.item_height + 5
                    
                    # Draw shutdown button
                    shutdown_rect = pygame.Rect(
                        self.padding,
                        button_y,
                        button_width,
                        button_height
                    )
                    pygame.draw.rect(panel_surface, (180, 60, 60), shutdown_rect)
                    shutdown_text = self.font.render("Shutdown", True, self.text_color)
                    text_x = self.padding + (button_width - shutdown_text.get_width()) // 2
                    text_y = button_y + (button_height - shutdown_text.get_height()) // 2
                    panel_surface.blit(shutdown_text, (text_x, text_y))
                    
                    # Draw restart button
                    restart_rect = pygame.Rect(
                        self.padding * 2 + button_width,
                        button_y,
                        button_width,
                        button_height
                    )
                    pygame.draw.rect(panel_surface, (60, 120, 180), restart_rect)
                    restart_text = self.font.render("Restart", True, self.text_color)
                    text_x = self.padding * 2 + button_width + (button_width - restart_text.get_width()) // 2
                    text_y = button_y + (button_height - restart_text.get_height()) // 2
                    panel_surface.blit(restart_text, (text_x, text_y))
                elif setting['type'] == 'action':
                    # Draw action button
                    button_rect = pygame.Rect(
                        self.padding,
                        self.padding + i * self.item_height + 5,
                        self.panel_width - 2 * self.padding,
                        self.item_height - 10
                    )
                    pygame.draw.rect(panel_surface, self.active_color, button_rect)
                    text = self.font.render(setting['name'], True, self.text_color)
                    text_rect = text.get_rect(center=button_rect.center)
                    panel_surface.blit(text, text_rect)
                else:
                    # Draw setting name
                    text = self.font.render(setting['name'], True, self.text_color)
                    panel_surface.blit(text, (self.padding, self.padding + i * self.item_height + 10))
                    
                    # Draw setting value
                    if setting['type'] == 'bool':
                        value_text = "On" if setting['value'] else "Off"
                        color = self.active_color if setting['value'] else self.text_color
                    elif setting['type'] == 'color_picker':
                        value_text = f"RGB{tuple(setting['value'])}"
                        color = self.text_color
                    elif setting['type'] == 'dropdown':
                        # Show shortened version of the checkpoint name
                        value_text = setting['value'].split('_')[0]
                        color = self.active_color
                    elif setting['type'] == 'select':
                        value_text = setting['value']
                        color = self.active_color
                    else:
                        continue  # Skip rendering value for other types
                    
                    value_surface = self.font.render(value_text, True, color)
                    value_x = self.panel_width - value_surface.get_width() - self.padding
                    panel_surface.blit(value_surface, (value_x, self.padding + i * self.item_height + 10))
            
            # Draw panel on main surface
            surface.blit(panel_surface, (self.panel_x, self.panel_y))
            
            # Draw dialog if visible
            self.dialog.draw(surface)
        
        # Draw notification if active
        if self.notification:
            current_time = time.time()
            if self.notification_duration is None or current_time - self.notification_start <= self.notification_duration:
                # Calculate fade out alpha for notifications
                alpha = 255
                if self.notification_duration is not None:
                    alpha = int(255 * (1 - (current_time - self.notification_start) / self.notification_duration))
                
                # Draw notification with wider width
                message_surface = pygame.Surface((500, 60), pygame.SRCALPHA)
                message_text = self.font.render(self.notification, True, (255, 255, 255))
                text_rect = message_text.get_rect(center=(250, 30))
                
                # Draw semi-transparent background
                pygame.draw.rect(message_surface, (40, 40, 40, min(200, alpha)), message_surface.get_rect(), border_radius=10)
                pygame.draw.rect(message_surface, (80, 80, 80, min(200, alpha)), message_surface.get_rect(), 2, border_radius=10)
                
                # Apply fade out to text
                message_text.set_alpha(alpha)
                message_surface.blit(message_text, text_rect)
                
                # Position at bottom center of screen
                message_x = (self.screen_width - 500) // 2
                message_y = self.screen_height - 80
                surface.blit(message_surface, (message_x, message_y))
            else:
                self.notification = None

    def _download_default_model(self):
        """Download the default Stable Diffusion 1.5 model if no models are present"""
        models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
        os.makedirs(models_dir, exist_ok=True)
        
        model_url = self.config.render['models']['default_model']['url']
        model_path = os.path.join(os.path.dirname(os.path.dirname(models_dir)), 
                                 self.config.render['models']['default_model']['path'])
        
        # Show downloading notification
        self.dialog.show_notification("Downloading Stable Diffusion 1.5...", duration=None)
        
        # Download with progress tracking
        response = requests.get(model_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(model_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        self.dialog.show_notification("Download complete!", duration=2)
        return self.config.render['models']['default_model']['path']

    def _get_available_models(self):
        """Scan the models directory for available checkpoints"""
        models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
        models = []
        if os.path.exists(models_dir):
            for file in os.listdir(models_dir):
                if file.endswith('.safetensors'):
                    models.append(os.path.join('models', file))
        
        if not models:
            # No models found, download default SD 1.5
            default_model = self._download_default_model()
            models.append(os.path.relpath(default_model, os.path.dirname(models_dir)))
            # Update config to use the new model
            self.config.update('render', 'checkpoint', models[0])
            
        return models 