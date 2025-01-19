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
        """Load configuration from config.yaml and local_config.yaml"""
        # Load base config
        config_path = Path('config.yaml')
        if not config_path.exists():
            raise FileNotFoundError("config.yaml not found in the current directory")
        
        with open(config_path, 'r') as f:
            self._base_config = yaml.safe_load(f)
            
        # Load local overrides if they exist
        local_path = Path('local_config.yaml')
        if local_path.exists():
            with open(local_path, 'r') as f:
                self._local_config = yaml.safe_load(f) or {}
        else:
            self._local_config = {}
    
    def save_local(self):
        """Save local configuration overrides to local_config.yaml"""
        local_path = Path('local_config.yaml')
        with open(local_path, 'w') as f:
            yaml.dump(self._local_config, f, default_flow_style=False, sort_keys=False)
    
    def reload(self):
        """Reload configuration from files"""
        self._load_config()
    
    def update(self, section, key, value):
        """Update a configuration value in local_config.yaml"""
        # Ensure section exists in local config
        if section not in self._local_config:
            self._local_config[section] = {}
        
        # Update the value
        self._local_config[section][key] = value
        self.save_local()
        return True
    
    def get(self, *keys, default=None):
        """Get a nested configuration value using dot notation, checking local overrides first"""
        # Try local config first
        value = self._local_config
        for key in keys:
            try:
                value = value[key]
                return value  # If found in local config, return it
            except (KeyError, TypeError):
                pass
        
        # Fall back to base config
        value = self._base_config
        for key in keys:
            try:
                value = value[key]
            except (KeyError, TypeError):
                return default
        return value
    
    def _merge_config_section(self, section_name):
        """Helper to merge a config section with its local overrides"""
        base = self._base_config.get(section_name, {}).copy()
        local = self._local_config.get(section_name, {})
        base.update(local)
        return base
    
    @property
    def display(self):
        return self._merge_config_section('display')
    
    @property
    def render(self):
        return self._merge_config_section('render')
    
    @property
    def clock(self):
        return self._merge_config_section('clock')
    
    @property
    def animation(self):
        return self._merge_config_section('animation')
    
    @property
    def enhancement(self):
        return self._merge_config_section('enhancement')
        
    @property
    def system(self):
        return self._merge_config_section('system')
        
    @property
    def prompts(self):
        return self._merge_config_section('prompts') 