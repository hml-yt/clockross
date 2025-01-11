import pygame
import math
from datetime import datetime
from ..config import Config

class ClockFace:
    def __init__(self, width, height):
        self.config = Config()
        self.width = width
        self.height = height
        self.center = (width // 2, height // 2)
        self.clock_radius = min(width, height) // 2 - self.config.clock['radius_margin']
        self.marker_length = self.config.clock['marker_length']
        self.hour_hand_length = self.clock_radius * self.config.clock['hour_hand_length_ratio']
        self.minute_hand_length = self.clock_radius * self.config.clock['minute_hand_length_ratio']
        self.second_hand_length = self.clock_radius * self.config.clock['second_hand_length_ratio']
        
        # Colors
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.gray = tuple(self.config.api['background_color'])
        self.transparent_white = (255, 255, 255, self.config.clock['overlay_opacity'])
        
        # Create surfaces
        self.api_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.overlay_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Initialize font for numbers
        self.font = pygame.font.Font(None, self.config.clock['font_size'])

    def draw_tapered_line(self, surface, color, start_pos, end_pos, start_width, end_width):
        """Draw a line that is wider at the start and narrower at the end"""
        angle = math.atan2(end_pos[1] - start_pos[1], end_pos[0] - start_pos[0])
        
        # Create points for a polygon
        points = []
        for t in range(0, 101, 5):
            t = t / 100
            width = start_width * (1 - t) + end_width * t
            x = start_pos[0] + (end_pos[0] - start_pos[0]) * t
            y = start_pos[1] + (end_pos[1] - start_pos[1]) * t
            points.append((
                x + math.cos(angle + math.pi/2) * width/2,
                y + math.sin(angle + math.pi/2) * width/2
            ))
        
        for t in range(100, -1, -5):
            t = t / 100
            width = start_width * (1 - t) + end_width * t
            x = start_pos[0] + (end_pos[0] - start_pos[0]) * t
            y = start_pos[1] + (end_pos[1] - start_pos[1]) * t
            points.append((
                x + math.cos(angle - math.pi/2) * width/2,
                y + math.sin(angle - math.pi/2) * width/2
            ))
        
        pygame.draw.polygon(surface, color, points)

    def draw_hour_marker(self, surface, hour, color, is_overlay=False):
        """Draw either a line marker or number for the given hour position"""
        angle = math.radians(hour * 360 / 12 - 90)
        
        if self.config.clock['use_numbers']:
            # Calculate position for number
            number_radius = self.clock_radius - self.marker_length - 10
            pos = (
                self.center[0] + number_radius * math.cos(angle),
                self.center[1] + number_radius * math.sin(angle)
            )
            # Convert 0 to 12
            hour_num = 12 if hour == 0 else hour
            
            # Create text surface
            if is_overlay:
                text = self.font.render(str(hour_num), True, (255, 255, 255))
                # Create a surface with per-pixel alpha
                alpha_surface = pygame.Surface(text.get_size(), pygame.SRCALPHA)
                # Fill with transparent color using the overlay opacity
                alpha_surface.fill((255, 255, 255, self.config.clock['overlay_opacity']))
                # Blit using the text as a mask
                alpha_surface.blit(text, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                text = alpha_surface
            else:
                text = self.font.render(str(hour_num), True, color)
            
            # Rotate the text
            rotation_angle = math.degrees(angle) + 90  # Add 90 to align text properly
            rotated_text = pygame.transform.rotate(text, -rotation_angle)
            
            # Get the rect of the rotated surface and position it
            text_rect = rotated_text.get_rect(center=pos)
            surface.blit(rotated_text, text_rect)
        else:
            # Draw traditional marker line
            start_pos = (
                self.center[0] + (self.clock_radius - self.marker_length) * math.cos(angle),
                self.center[1] + (self.clock_radius - self.marker_length) * math.sin(angle)
            )
            end_pos = (
                self.center[0] + self.clock_radius * math.cos(angle),
                self.center[1] + self.clock_radius * math.sin(angle)
            )
            pygame.draw.line(surface, color, start_pos, end_pos, 
                           self.config.clock['marker_width'])

    def draw_clock_hands(self, hours, minutes):
        """Draw the hour and minute hands on both surfaces"""
        # Clear the surfaces
        self.api_surface.fill((0, 0, 0, 0))
        self.overlay_surface.fill((0, 0, 0, 0))
        
        # Fill API surface with background color from current config
        self.gray = tuple(self.config.api['background_color'])
        self.api_surface.fill((*self.gray, 255))
        
        # Draw hour markers
        for hour in range(12):
            if not self.config.clock['render_on_screen']:
                self.draw_hour_marker(self.api_surface, hour, self.white)
            if self.config.clock['render_on_screen']:
                self.draw_hour_marker(self.overlay_surface, hour, self.transparent_white, True)
        
        # Hour hand
        hour_angle = math.radians((hours % 12 + minutes / 60) * 360 / 12 - 90)
        hour_end = (
            self.center[0] + self.hour_hand_length * math.cos(hour_angle),
            self.center[1] + self.hour_hand_length * math.sin(hour_angle)
        )
        hw = self.config.clock['hour_hand_width']
        self.draw_tapered_line(self.api_surface, self.white, self.center, hour_end, hw[0], hw[1])
        
        # Minute hand
        minute_angle = math.radians(minutes * 360 / 60 - 90)
        minute_end = (
            self.center[0] + self.minute_hand_length * math.cos(minute_angle),
            self.center[1] + self.minute_hand_length * math.sin(minute_angle)
        )
        mw = self.config.clock['minute_hand_width']
        self.draw_tapered_line(self.api_surface, self.white, self.center, minute_end, mw[0], mw[1])
        
        # Draw center dot
        pygame.draw.circle(self.api_surface, self.white, self.center, 10)
        
        return self.api_surface

    def draw_clock_overlay(self, surface):
        """Draw clock face overlay with hour markers and outer circle"""
        # Draw outer circle and markers on screen if configured
        if self.config.clock['render_on_screen']:
            # Draw outer circle
            pygame.draw.circle(surface, self.transparent_white, self.center, self.clock_radius, 
                             self.config.clock['marker_width'])
            
            # Draw hour markers or numbers
            for hour in range(12):
                self.draw_hour_marker(surface, hour, self.transparent_white, is_overlay=True)

    def draw_seconds_hand(self, surface, seconds, color):
        """Draw the seconds hand with the given color"""
        seconds_angle = math.radians(seconds * 360 / 60 - 90)
        seconds_end = (
            self.center[0] + self.second_hand_length * math.cos(seconds_angle),
            self.center[1] + self.second_hand_length * math.sin(seconds_angle)
        )
        sw = self.config.clock['second_hand_width']
        self.draw_tapered_line(surface, color, self.center, seconds_end, sw[0], sw[1]) 