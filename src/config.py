import yaml
from pathlib import Path

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from config.yaml and dynamic_settings.yaml"""
        # Load base config
        config_path = Path('config.yaml')
        if not config_path.exists():
            raise FileNotFoundError("config.yaml not found in the current directory")
        
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
            
        # Load dynamic settings if exists, otherwise use defaults from base config
        dynamic_path = Path('dynamic_settings.yaml')
        if dynamic_path.exists():
            with open(dynamic_path, 'r') as f:
                self._dynamic = yaml.safe_load(f)
        else:
            # Initialize dynamic settings with values from base config
            self._dynamic = {
                'clock': {
                    'use_numbers': self._config['clock']['use_numbers']
                },
                'api': {
                    'background_color': self._config['api']['background_color'],
                    'checkpoint': self._config['api']['checkpoint']
                }
            }
            self.save_dynamic()
    
    def save(self):
        """Save current base configuration to file"""
        config_path = Path('config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)
    
    def save_dynamic(self):
        """Save dynamic settings to separate file"""
        dynamic_path = Path('dynamic_settings.yaml')
        with open(dynamic_path, 'w') as f:
            yaml.dump(self._dynamic, f, default_flow_style=False, sort_keys=False)
    
    def reload(self):
        """Reload configuration from files"""
        self._load_config()
    
    def update(self, section, key, value):
        """Update a configuration value and save to appropriate file"""
        # Always save display_mode to dynamic settings
        if section == 'clock' and key == 'display_mode':
            if 'clock' not in self._dynamic:
                self._dynamic['clock'] = {}
            self._dynamic['clock']['display_mode'] = value
            self.save_dynamic()
            return True
        # Check if this is a dynamic setting
        if section in self._dynamic and key in self._dynamic[section]:
            self._dynamic[section][key] = value
            self.save_dynamic()
            return True
        # Fall back to base config
        elif section in self._config and key in self._config[section]:
            self._config[section][key] = value
            self.save()
            return True
        return False
    
    def get(self, *keys, default=None):
        """Get a nested configuration value using dot notation, checking dynamic settings first"""
        # Try dynamic settings first
        value = self._dynamic
        for key in keys:
            try:
                value = value[key]
                return value  # If found in dynamic settings, return it
            except (KeyError, TypeError):
                pass
        
        # Fall back to base config
        value = self._config
        for key in keys:
            try:
                value = value[key]
            except (KeyError, TypeError):
                return default
        return value
    
    @property
    def display(self):
        return self._config['display']
    
    @property
    def api(self):
        # Merge base and dynamic API settings
        base_api = self._config['api'].copy()
        if 'api' in self._dynamic:
            base_api.update(self._dynamic['api'])
        return base_api
    
    @property
    def clock(self):
        # Merge base and dynamic clock settings
        base_clock = self._config['clock'].copy()
        # Get display_mode from dynamic settings if it exists, otherwise use default from base config
        if 'clock' in self._dynamic:
            base_clock.update(self._dynamic['clock'])
        return base_clock
    
    @property
    def animation(self):
        return self._config['animation']
    
    @property
    def enhancement(self):
        return self._config['enhancement']
        
    @property
    def system(self):
        return self._config['system'] 