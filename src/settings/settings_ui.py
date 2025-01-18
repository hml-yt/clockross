import pygame
import pygame.gfxdraw
import random
import os
import json
from datetime import datetime
from ..config import Config
import time

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
            alpha = int(255 * (1 - (time.time() - self.start_time) / self.duration))
            
            # Draw notification
            message_surface = pygame.Surface((300, 60), pygame.SRCALPHA)
            message_text = self.font.render(self.message, True, (255, 255, 255))
            text_rect = message_text.get_rect(center=(150, 30))
            
            # Draw semi-transparent background
            pygame.draw.rect(message_surface, (40, 40, 40, min(200, alpha)), message_surface.get_rect(), border_radius=10)
            pygame.draw.rect(message_surface, (80, 80, 80, min(200, alpha)), message_surface.get_rect(), 2, border_radius=10)
            
            # Apply fade out to text
            message_text.set_alpha(alpha)
            message_surface.blit(message_text, text_rect)
            
            # Position at bottom center of screen
            message_x = (self.screen_width - 300) // 2
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
        
        # UI settings
        self.padding = 30
        self.item_height = 60
        self.font_size = 32
        self.font = pygame.font.Font(None, self.font_size)
        self.panel_width = 600
        
        # Dialog system
        self.dialog = Dialog(screen_width, screen_height, self.font)
        
        # Colors
        self.panel_color = (30, 30, 30, 220)
        self.text_color = (255, 255, 255)
        self.active_color = (0, 120, 255)
        
        # Font options for random selection
        self.font_options = ["Arial", "Helvetica", "Times New Roman", "Brush Script MT"]
        
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
                'name': 'Background Color',
                'key': ('api', 'background_color'),
                'type': 'color',
                'value': self.config.api['background_color']
            },
            {
                'name': 'Model Checkpoint',
                'key': ('api', 'checkpoint'),
                'type': 'select',
                'value': self.config.api['checkpoint'],
                'options': self.config.api['checkpoints']
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

    def toggle(self):
        """Toggle settings visibility"""
        if self.visible:  # If we're closing the panel
            self.visible = False  # Hide dialog first
            if self.checkpoint_changed and self.background_updater:
                self.dialog.show_notification("Loading new pipeline...", duration=3)
                self.background_updater.reload_pipeline()  # Reload the pipeline with new checkpoint
                self.background_updater.last_attempt = 0  # Force update
                self.checkpoint_changed = False
            return
        self.visible = True
    
    def handle_click(self, pos):
        """Handle mouse click at the given position"""
        if not self.visible:
            return False
            
        # Let dialog handle clicks first if visible
        if self.dialog.visible:
            return self.dialog.handle_click(pos)
            
        # Check if click is outside panel
        if not (self.panel_x <= pos[0] <= self.panel_x + self.panel_width and
                self.panel_y <= pos[1] <= self.panel_y + self.panel_height):
            self.visible = False
            if self.checkpoint_changed and self.background_updater:
                self.dialog.show_notification("Loading new pipeline...", duration=3)
                self.background_updater.reload_pipeline()  # Reload the pipeline with new checkpoint
                self.background_updater.last_attempt = 0  # Force update
                self.checkpoint_changed = False
            return True
            
        # Calculate which setting was clicked
        relative_y = pos[1] - self.panel_y - self.padding
        index = int(relative_y // self.item_height)
        
        if 0 <= index < len(self.settings):
            setting = self.settings[index]
            if setting['type'] == 'action' and setting['action'] == 'snapshot':
                print("Taking snapshot")
                self.take_screenshot()
                return True
            elif setting['type'] == 'system_row':
                # Calculate button positions exactly as drawn
                button_width = (self.panel_width - 3 * self.padding) // 2
                button_height = self.item_height - 10
                button_y = self.panel_y + self.padding + index * self.item_height + 5
                
                # Check shutdown button
                shutdown_rect = pygame.Rect(
                    self.panel_x + self.padding,
                    button_y,
                    button_width,
                    button_height
                )
                if shutdown_rect.collidepoint(pos[0], pos[1]):
                    def handle_shutdown(confirmed):
                        if confirmed:
                            os.system(self.config.system["shutdown_cmd"])
                    self.dialog.show_confirmation("Confirm Shutdown", "Are you sure?", handle_shutdown)
                    return True
                
                # Check restart button
                restart_rect = pygame.Rect(
                    self.panel_x + self.padding * 2 + button_width,
                    button_y,
                    button_width,
                    button_height
                )
                if restart_rect.collidepoint(pos[0], pos[1]):
                    def handle_restart(confirmed):
                        if confirmed:
                            os.system(self.config.system["restart_cmd"])
                    self.dialog.show_confirmation("Confirm Restart", "Are you sure?", handle_restart)
                    return True
            elif setting['type'] == 'bool':
                # Toggle boolean value
                setting['value'] = not setting['value']
                # Update config
                self.config.update(setting['key'][0], setting['key'][1], setting['value'])
                # Force background update if it was the use_numbers setting
                if setting['key'][1] == 'use_numbers' and self.background_updater:
                    self.background_updater.last_attempt = 0  # Force update
            elif setting['type'] == 'color':
                # Cycle through some preset colors
                presets = [(25, 25, 25), (40, 40, 40), (75, 75, 75)]
                current = tuple(setting['value'])
                next_index = (presets.index(current) + 1) % len(presets) if current in presets else 0
                setting['value'] = list(presets[next_index])
                # Update config
                self.config.update(setting['key'][0], setting['key'][1], setting['value'])
                # Force background update if it was the background color setting
                if setting['key'][1] == 'background_color' and self.background_updater:
                    self.background_updater.last_attempt = 0  # Force update
            elif setting['type'] == 'select':
                # Cycle through options
                current_index = setting['options'].index(setting['value'])
                next_index = (current_index + 1) % len(setting['options'])
                setting['value'] = setting['options'][next_index]
                
                # Handle random font selection
                if setting['key'][1] == 'font':
                    if setting['value'] == 'Random':
                        random_font = random.choice(self.font_options)
                        self.config.update(setting['key'][0], setting['key'][1], random_font)
                    else:
                        self.config.update(setting['key'][0], setting['key'][1], setting['value'])
                    # Update the clock face font
                    if self.clock_face:
                        self.clock_face.update_font()
                else:
                    self.config.update(setting['key'][0], setting['key'][1], setting['value'])
                    # Mark checkpoint as changed if it was the checkpoint setting
                    if setting['key'][1] == 'checkpoint':
                        self.checkpoint_changed = True
                        self.dialog.show_notification(f"Selected checkpoint: {setting['value'].split('_')[0]}")
        
        return True
    
    def take_screenshot(self):
        """Take screenshots of the clock face, hands, and save API request"""
        if not self.surface_manager:
            return
        self.surface_manager.save_snapshot()
        self.dialog.show_notification("Snapshot Saved!")

    def draw(self, surface):
        """Draw the settings UI if visible"""
        if not self.visible:
            return
            
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
                elif setting['type'] == 'color':
                    value_text = f"RGB{tuple(setting['value'])}"
                    color = self.text_color
                elif setting['type'] == 'select':
                    # Show shortened version of the checkpoint name
                    value_text = setting['value'].split('_')[0]
                    color = self.active_color
                
                value_surface = self.font.render(value_text, True, color)
                value_x = self.panel_width - value_surface.get_width() - self.padding
                panel_surface.blit(value_surface, (value_x, self.padding + i * self.item_height + 10))
                
        # Draw panel on main surface
        surface.blit(panel_surface, (self.panel_x, self.panel_y))
        
        # Draw dialog if visible
        self.dialog.draw(surface) 