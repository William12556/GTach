"""
OBDII Home Directory Management

Provides centralized path management for configuration, logs, and data directories.
Supports OBDII_HOME environment variable with fallback to development/installation paths.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Union


class OBDIIHome:
    """
    Centralized path management for OBDII application directories.
    
    Handles OBDII_HOME environment variable and provides fallback paths
    for development and production environments.
    """
    
    def __init__(self):
        self._home_path: Optional[Path] = None
        self._is_development: Optional[bool] = None
    
    @property
    def home_path(self) -> Path:
        """Get the OBDII home directory path."""
        if self._home_path is None:
            self._home_path = self._determine_home_path()
        return self._home_path
    
    @property
    def config_dir(self) -> Path:
        """Get the configuration directory path."""
        return self.home_path / "config"
    
    @property
    def logs_dir(self) -> Path:
        """Get the logs directory path."""
        return self.home_path / "logs"
    
    @property
    def data_dir(self) -> Path:
        """Get the data directory path."""
        return self.home_path / "data"
    
    @property
    def cache_dir(self) -> Path:
        """Get the cache directory path."""
        return self.home_path / "cache"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        if self._is_development is None:
            self._is_development = self._detect_development_environment()
        return self._is_development
    
    def _determine_home_path(self) -> Path:
        """
        Determine OBDII home directory from environment or fallback paths.
        
        Priority order:
        1. OBDII_HOME environment variable
        2. Development environment (project root)
        3. User installation (~/.local/share/obdii)
        4. System installation (/opt/obdii or /usr/local/share/obdii)
        """
        # Check environment variable first
        env_home = os.environ.get('OBDII_HOME')
        if env_home:
            path = Path(env_home).expanduser().resolve()
            if path.exists() or self._can_create_directory(path):
                return path
        
        # Development environment (project root)
        project_root = self._find_project_root()
        if project_root and self.is_development:
            return project_root
        
        # User installation directory
        user_home = Path.home() / ".local" / "share" / "obdii"
        if user_home.exists() or self._can_create_directory(user_home):
            return user_home
        
        # System installation directories
        system_paths = [
            Path("/opt/obdii"),
            Path("/usr/local/share/obdii"),
            Path("/usr/share/obdii")
        ]
        
        for path in system_paths:
            if path.exists():
                return path
        
        # Fallback to user directory (create if needed)
        self._ensure_directory_exists(user_home)
        return user_home
    
    def _find_project_root(self) -> Optional[Path]:
        """Find the project root directory by looking for key files."""
        current = Path(__file__).parent
        
        # Look for project markers
        markers = ['pyproject.toml', 'setup.py', '.git', 'src/obdii']
        
        while current != current.parent:
            if any((current / marker).exists() for marker in markers):
                return current
            current = current.parent
        
        return None
    
    def _detect_development_environment(self) -> bool:
        """Detect if running in development environment."""
        # Check if running from source directory
        current_file = Path(__file__).resolve()
        if 'src/obdii' in str(current_file):
            return True
        
        # Check for development indicators
        project_root = self._find_project_root()
        if project_root:
            dev_indicators = [
                project_root / "src" / "obdii",
                project_root / ".git",
                project_root / "pyproject.toml"
            ]
            return any(indicator.exists() for indicator in dev_indicators)
        
        # Check if installed in editable mode
        try:
            import obdii
            if hasattr(obdii, '__path__') and obdii.__path__:
                path = Path(obdii.__path__[0])
                return 'src' in str(path) or '.egg-link' in str(path)
        except ImportError:
            pass
        
        return False
    
    def _can_create_directory(self, path: Path) -> bool:
        """Check if directory can be created."""
        try:
            # Try to create parent directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            return True
        except (OSError, PermissionError):
            return False
    
    def _ensure_directory_exists(self, path: Path) -> None:
        """Ensure directory exists, creating if necessary."""
        try:
            path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Cannot create directory {path}: {e}")
    
    def ensure_directories(self) -> None:
        """Ensure all OBDII directories exist."""
        directories = [
            self.config_dir,
            self.logs_dir,
            self.data_dir,
            self.cache_dir
        ]
        
        for directory in directories:
            self._ensure_directory_exists(directory)
    
    def get_config_file(self, filename: str) -> Path:
        """Get path to configuration file."""
        return self.config_dir / filename
    
    def get_log_file(self, filename: str) -> Path:
        """Get path to log file."""
        return self.logs_dir / filename
    
    def get_data_file(self, filename: str) -> Path:
        """Get path to data file."""
        return self.data_dir / filename
    
    def get_cache_file(self, filename: str) -> Path:
        """Get path to cache file."""
        return self.cache_dir / filename
    
    def get_info(self) -> dict:
        """Get information about current path configuration."""
        return {
            'home_path': str(self.home_path),
            'config_dir': str(self.config_dir),
            'logs_dir': str(self.logs_dir),
            'data_dir': str(self.data_dir),
            'cache_dir': str(self.cache_dir),
            'is_development': self.is_development,
            'obdii_home_env': os.environ.get('OBDII_HOME'),
            'project_root': str(self._find_project_root()) if self._find_project_root() else None
        }


# Global instance for convenient access
_obdii_home = OBDIIHome()

# Convenience functions for common operations
def get_home_path() -> Path:
    """Get the OBDII home directory path."""
    return _obdii_home.home_path

def get_config_dir() -> Path:
    """Get the configuration directory path."""
    return _obdii_home.config_dir

def get_logs_dir() -> Path:
    """Get the logs directory path."""
    return _obdii_home.logs_dir

def get_data_dir() -> Path:
    """Get the data directory path."""
    return _obdii_home.data_dir

def get_cache_dir() -> Path:
    """Get the cache directory path."""
    return _obdii_home.cache_dir

def get_config_file(filename: str) -> Path:
    """Get path to configuration file."""
    return _obdii_home.get_config_file(filename)

def get_log_file(filename: str) -> Path:
    """Get path to log file."""
    return _obdii_home.get_log_file(filename)

def get_data_file(filename: str) -> Path:
    """Get path to data file."""
    return _obdii_home.get_data_file(filename)

def get_cache_file(filename: str) -> Path:
    """Get path to cache file."""
    return _obdii_home.get_cache_file(filename)

def ensure_directories() -> None:
    """Ensure all OBDII directories exist."""
    _obdii_home.ensure_directories()

def is_development() -> bool:
    """Check if running in development environment."""
    return _obdii_home.is_development

def get_path_info() -> dict:
    """Get information about current path configuration."""
    return _obdii_home.get_info()


if __name__ == "__main__":
    # CLI for testing and debugging
    import json
    
    if len(sys.argv) > 1 and sys.argv[1] == "--info":
        print(json.dumps(get_path_info(), indent=2))
    else:
        print(f"OBDII Home: {get_home_path()}")
        print(f"Config Dir: {get_config_dir()}")
        print(f"Logs Dir: {get_logs_dir()}")
        print(f"Data Dir: {get_data_dir()}")
        print(f"Cache Dir: {get_cache_dir()}")
        print(f"Development: {is_development()}")