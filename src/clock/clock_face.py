import pygame
import math
from datetime import datetime

class ClockFace:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.center = (width // 2, height // 2)
        self.clock_radius = min(width, height) // 2 - 20
        self.marker_length = 30
        self.hour_hand_length = self.clock_radius * 0.6
        self.minute_hand_length = self.clock_radius * 0.8
        self.second_hand_length = self.clock_radius * 0.9
        
        # Colors
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.gray = (25, 25, 25)
        self.transparent_white = (255, 255, 255, 75)
        
        # Create surfaces
        self.api_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.overlay_surface = pygame.Surface((width, height), pygame.SRCALPHA)

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

    def draw_clock_hands(self, hours, minutes):
        """Draw clock hands for API only"""
        self.api_surface.fill(self.gray)
        
        # Draw clock circle
        pygame.draw.circle(self.api_surface, self.white, self.center, self.clock_radius, 3)
        
        # Hour hand
        hour_angle = math.radians((hours % 12 + minutes / 60) * 360 / 12 - 90)
        hour_end = (
            self.center[0] + self.hour_hand_length * math.cos(hour_angle),
            self.center[1] + self.hour_hand_length * math.sin(hour_angle)
        )
        self.draw_tapered_line(self.api_surface, self.white, self.center, hour_end, 24, 6)
        
        # Minute hand
        minute_angle = math.radians(minutes * 360 / 60 - 90)
        minute_end = (
            self.center[0] + self.minute_hand_length * math.cos(minute_angle),
            self.center[1] + self.minute_hand_length * math.sin(minute_angle)
        )
        self.draw_tapered_line(self.api_surface, self.white, self.center, minute_end, 16, 4)
        
        # Draw hour markers
        for hour in range(12):
            angle = math.radians(hour * 360 / 12 - 90)
            start_pos = (
                self.center[0] + (self.clock_radius - self.marker_length) * math.cos(angle),
                self.center[1] + (self.clock_radius - self.marker_length) * math.sin(angle)
            )
            end_pos = (
                self.center[0] + self.clock_radius * math.cos(angle),
                self.center[1] + self.clock_radius * math.sin(angle)
            )
            pygame.draw.line(self.api_surface, self.white, start_pos, end_pos, 3)
        
        # Draw center dot
        pygame.draw.circle(self.api_surface, self.white, self.center, 10)
        
        return self.api_surface

    def draw_clock_overlay(self, surface):
        """Draw clock face overlay with hour markers and outer circle"""
        # Draw outer circle
        pygame.draw.circle(surface, self.transparent_white, self.center, self.clock_radius, 3)
        
        # Draw hour markers
        for hour in range(12):
            angle = math.radians(hour * 360 / 12 - 90)
            start_pos = (
                self.center[0] + (self.clock_radius - self.marker_length) * math.cos(angle),
                self.center[1] + (self.clock_radius - self.marker_length) * math.sin(angle)
            )
            end_pos = (
                self.center[0] + self.clock_radius * math.cos(angle),
                self.center[1] + self.clock_radius * math.sin(angle)
            )
            pygame.draw.line(surface, self.transparent_white, start_pos, end_pos, 3)

    def draw_seconds_hand(self, surface, seconds, color):
        """Draw the seconds hand with the given color"""
        seconds_angle = math.radians(seconds * 360 / 60 - 90)
        seconds_end = (
            self.center[0] + self.second_hand_length * math.cos(seconds_angle),
            self.center[1] + self.second_hand_length * math.sin(seconds_angle)
        )
        self.draw_tapered_line(surface, color, self.center, seconds_end, 4, 1) 