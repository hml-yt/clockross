import pygame
import pygame.gfxdraw
import random
from ..config import Config

class SettingsUI:
    def __init__(self, screen_width, screen_height, background_updater=None, clock_face=None):
        self.config = Config()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        self.background_updater = background_updater
        self.clock_face = clock_face
        self.checkpoint_changed = False
        self.settings = [
            {
                'name': 'Render on Screen',
                'key': ('clock', 'render_on_screen'),
                'type': 'bool',
                'value': self.config.clock['render_on_screen']
            },
            {
                'name': 'Use Numbers',
                'key': ('clock', 'use_numbers'),
                'type': 'bool',
                'value': self.config.clock['use_numbers']
            },
            {
                'name': 'Font',
                'key': ('clock', 'font'),
                'type': 'select',
                'value': self.config.clock['font'],
                'options': [
                    "Arial",
                    "Helvetica",
                    "Times New Roman",
                    "Brush Script MT",
                    "Random"
                ]
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
                'options': [
                    "abstractPhoto_abcevereMix_82372",
                    "revAnimated_v2Pruned_393004",
                    "dreamlikeDiffusion10_10_72",
                    "v1-5-pruned-emaonly"
                ]
            }
        ]
        
        # Font options for random selection
        self.font_options = ["Arial", "Helvetica", "Times New Roman", "Brush Script MT"]
        
        # UI settings
        self.padding = 20
        self.item_height = 40
        self.font_size = 24
        self.font = pygame.font.Font(None, self.font_size)
        self.panel_width = 400  # Increased width to accommodate longer text
        self.panel_height = len(self.settings) * self.item_height + 2 * self.padding
        
        # Calculate panel position (centered)
        self.panel_x = (screen_width - self.panel_width) // 2
        self.panel_y = (screen_height - self.panel_height) // 2
        
        # Colors
        self.panel_color = (30, 30, 30, 220)
        self.text_color = (255, 255, 255)
        self.hover_color = (60, 60, 60)
        self.active_color = (0, 120, 255)
        
        # Track hover state
        self.hover_index = -1
    
    def toggle(self):
        """Toggle settings visibility"""
        if self.visible:  # If we're closing the panel
            if self.checkpoint_changed and self.background_updater:
                self.background_updater.last_attempt = 0  # Force update
                self.checkpoint_changed = False
        self.visible = not self.visible
    
    def handle_click(self, pos):
        """Handle mouse click at the given position"""
        if not self.visible:
            return False
        
        # Check if click is inside panel
        if not (self.panel_x <= pos[0] <= self.panel_x + self.panel_width and
                self.panel_y <= pos[1] <= self.panel_y + self.panel_height):
            if self.checkpoint_changed and self.background_updater:
                self.background_updater.last_attempt = 0  # Force update
                self.checkpoint_changed = False
            self.visible = False
            return True
        
        # Calculate which setting was clicked
        relative_y = pos[1] - self.panel_y - self.padding
        index = int(relative_y // self.item_height)
        
        if 0 <= index < len(self.settings):
            setting = self.settings[index]
            if setting['type'] == 'bool':
                # Toggle boolean value
                setting['value'] = not setting['value']
                # Update config
                self.config.update(setting['key'][0], setting['key'][1], setting['value'])
            elif setting['type'] == 'color':
                # Cycle through some preset colors
                presets = [(25, 25, 25), (40, 40, 40), (75, 75, 75)]
                current = tuple(setting['value'])
                next_index = (presets.index(current) + 1) % len(presets) if current in presets else 0
                setting['value'] = list(presets[next_index])
                # Update config
                self.config.update(setting['key'][0], setting['key'][1], setting['value'])
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
        
        return True
    
    def handle_motion(self, pos):
        """Handle mouse motion for hover effects"""
        if not self.visible:
            return
        
        if (self.panel_x <= pos[0] <= self.panel_x + self.panel_width and
                self.panel_y <= pos[1] <= self.panel_y + self.panel_height):
            relative_y = pos[1] - self.panel_y - self.padding
            self.hover_index = int(relative_y // self.item_height)
            if not (0 <= self.hover_index < len(self.settings)):
                self.hover_index = -1
        else:
            self.hover_index = -1
    
    def draw(self, surface):
        """Draw the settings UI if visible"""
        if not self.visible:
            return
        
        # Draw semi-transparent panel background
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
            
            # Draw hover highlight
            if i == self.hover_index:
                pygame.draw.rect(panel_surface, self.hover_color, item_rect)
            
            # Draw setting name
            text = self.font.render(setting['name'], True, self.text_color)
            text_y = self.padding + i * self.item_height + (self.item_height - text.get_height()) // 2
            panel_surface.blit(text, (self.padding, text_y))
            
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
            panel_surface.blit(value_surface, (value_x, text_y))
        
        # Draw panel on main surface
        surface.blit(panel_surface, (self.panel_x, self.panel_y)) 