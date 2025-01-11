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
        """Load configuration from config.yaml"""
        config_path = Path('config.yaml')
        if not config_path.exists():
            raise FileNotFoundError("config.yaml not found in the current directory")
        
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
    
    def reload(self):
        """Reload configuration from file"""
        self._load_config()
    
    @property
    def display(self):
        return self._config['display']
    
    @property
    def api(self):
        return self._config['api']
    
    @property
    def clock(self):
        return self._config['clock']
    
    @property
    def animation(self):
        return self._config['animation']
    
    @property
    def enhancement(self):
        return self._config['enhancement']
    
    def get(self, *keys, default=None):
        """Get a nested configuration value using dot notation"""
        value = self._config
        for key in keys:
            try:
                value = value[key]
            except (KeyError, TypeError):
                return default
        return value 