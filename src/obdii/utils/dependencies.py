#!/usr/bin/env python3
"""
Dependency validation system for OBDII display application.
Validates platform-specific requirements and provides clear error messages.
"""

import sys
import os
import logging
import importlib.util
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum, auto

class DependencyType(Enum):
    """Types of dependencies"""
    REQUIRED = "required"
    OPTIONAL = "optional"
    PLATFORM_SPECIFIC = "platform_specific"
    DEVELOPMENT = "development"

class ValidationResult(Enum):
    """Validation result status"""
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()
    FATAL = auto()

@dataclass
class DependencyInfo:
    """Information about a dependency"""
    name: str
    import_name: str
    dependency_type: DependencyType
    platforms: List[str] = field(default_factory=list)  # Empty means all platforms
    version_check: Optional[str] = None
    install_hint: str = ""
    description: str = ""
    alternatives: List[str] = field(default_factory=list)

@dataclass
class ValidationReport:
    """Dependency validation report"""
    name: str
    dependency_info: DependencyInfo
    result: ValidationResult
    available: bool
    version: Optional[str] = None
    error_message: Optional[str] = None
    install_command: Optional[str] = None

class DependencyValidator:
    """Validates application dependencies with platform-specific requirements"""
    
    def __init__(self, debug: bool = False):
        """Initialize dependency validator
        
        Args:
            debug: Enable debug logging and detailed reporting
        """
        self.debug = debug
        self.logger = logging.getLogger('DependencyValidator')
        self.platform_info = self._detect_platform()
        self.reports: List[ValidationReport] = []
        
        # Define all dependencies
        self.dependencies = self._define_dependencies()
        
        if self.debug:
            self.logger.setLevel(logging.DEBUG)
    
    def _detect_platform(self) -> Dict[str, Any]:
        """Detect current platform and capabilities"""
        # Get platform info directly to avoid import conflicts
        import os
        import sys
        
        # Get system info directly from os.uname() and sys
        try:
            uname = os.uname()
            system = uname.sysname
            machine = uname.machine
        except AttributeError:
            # Fallback for Windows
            system = os.name
            machine = 'unknown'
        
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        platform_info = {
            'system': system,
            'machine': machine,
            'python_version': python_version,
            'is_raspberry_pi': False,
            'is_macos': system == 'Darwin',
            'is_linux': system == 'Linux',
            'is_development': False
        }
        
        # Detect Raspberry Pi
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'BCM' in cpuinfo or 'Raspberry Pi' in cpuinfo:
                    platform_info['is_raspberry_pi'] = True
        except (FileNotFoundError, PermissionError):
            pass
        
        # Determine if this is a development environment
        platform_info['is_development'] = (
            platform_info['is_macos'] or 
            (platform_info['is_linux'] and not platform_info['is_raspberry_pi'])
        )
        
        if self.debug:
            self.logger.debug(f"Platform detection: {platform_info}")
        
        return platform_info
    
    def _define_dependencies(self) -> List[DependencyInfo]:
        """Define all application dependencies with platform-specific requirements"""
        return [
            # Core Python libraries
            DependencyInfo(
                name="Python Standard Library",
                import_name="os",
                dependency_type=DependencyType.REQUIRED,
                description="Python standard library modules"
            ),
            
            # PyGame for display
            DependencyInfo(
                name="PyGame",
                import_name="pygame",
                dependency_type=DependencyType.REQUIRED,
                install_hint="pip install pygame",
                description="Graphics and display rendering"
            ),
            
            # YAML configuration
            DependencyInfo(
                name="PyYAML",
                import_name="yaml",
                dependency_type=DependencyType.REQUIRED,
                install_hint="pip install PyYAML",
                description="YAML configuration file support"
            ),
            
            # Serial communication
            DependencyInfo(
                name="PySerial",
                import_name="serial",
                dependency_type=DependencyType.REQUIRED,
                install_hint="pip install pyserial",
                description="Serial communication for OBD-II interface"
            ),
            
            # Bluetooth communication
            DependencyInfo(
                name="PyBluez",
                import_name="bluetooth",
                dependency_type=DependencyType.OPTIONAL,
                install_hint="pip install pybluez",
                description="Bluetooth communication support"
            ),
            
            # Raspberry Pi GPIO (Pi-specific)
            DependencyInfo(
                name="RPi.GPIO",
                import_name="RPi.GPIO",
                dependency_type=DependencyType.PLATFORM_SPECIFIC,
                platforms=["raspberry_pi"],
                install_hint="pip install RPi.GPIO",
                description="Raspberry Pi GPIO control"
            ),
            
            # HyperPixel display (Pi-specific)
            DependencyInfo(
                name="HyperPixel2R",
                import_name="hyperpixel2r",
                dependency_type=DependencyType.PLATFORM_SPECIFIC,
                platforms=["raspberry_pi"],
                install_hint="Follow HyperPixel2R installation guide",
                description="HyperPixel 2.1 Round display driver"
            ),
            
            # Development dependencies
            DependencyInfo(
                name="Requests",
                import_name="requests",
                dependency_type=DependencyType.DEVELOPMENT,
                platforms=["development"],
                install_hint="pip install requests",
                description="HTTP library for development tools"
            ),
            
            # Math libraries
            DependencyInfo(
                name="Math",
                import_name="math",
                dependency_type=DependencyType.REQUIRED,
                description="Mathematical functions"
            ),
            
            # Threading
            DependencyInfo(
                name="Threading",
                import_name="threading",
                dependency_type=DependencyType.REQUIRED,
                description="Multi-threading support"
            ),
            
            # Time utilities
            DependencyInfo(
                name="Time",
                import_name="time",
                dependency_type=DependencyType.REQUIRED,
                description="Time and timing utilities"
            ),
            
            # Logging
            DependencyInfo(
                name="Logging",
                import_name="logging",
                dependency_type=DependencyType.REQUIRED,
                description="Application logging"
            ),
        ]
    
    def _should_check_dependency(self, dep: DependencyInfo) -> bool:
        """Determine if a dependency should be checked on current platform"""
        # Always check required dependencies
        if dep.dependency_type == DependencyType.REQUIRED:
            return True
        
        # Check platform-specific dependencies
        if dep.dependency_type == DependencyType.PLATFORM_SPECIFIC:
            if not dep.platforms:
                return True  # No platform restriction
            
            if "raspberry_pi" in dep.platforms and self.platform_info['is_raspberry_pi']:
                return True
            if "macos" in dep.platforms and self.platform_info['is_macos']:
                return True
            if "linux" in dep.platforms and self.platform_info['is_linux']:
                return True
            
            return False
        
        # Check development dependencies
        if dep.dependency_type == DependencyType.DEVELOPMENT:
            if not dep.platforms:
                return True
            
            if "development" in dep.platforms and self.platform_info['is_development']:
                return True
            
            return False
        
        # Check optional dependencies
        if dep.dependency_type == DependencyType.OPTIONAL:
            return True
        
        return False
    
    def _check_import(self, import_name: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Check if a module can be imported and get version info
        
        Enhanced to properly check virtual environment installations and provide
        detailed debugging information for dependency detection issues.
        
        Returns:
            Tuple of (available, version, error_message)
        """
        if self.debug:
            self.logger.debug(f"Checking import for: {import_name}")
            self.logger.debug(f"Python executable: {sys.executable}")
            self.logger.debug(f"Python path: {sys.path[:3]}...")  # First 3 entries
            
            # Check if we're in a virtual environment
            venv_info = self._detect_virtual_environment()
            if venv_info['in_venv']:
                self.logger.debug(f"Virtual environment detected: {venv_info['venv_path']}")
            else:
                self.logger.debug("Not in virtual environment (or not detected)")
        
        try:
            # Try to import the module
            module = importlib.import_module(import_name)
            
            # Try to get version information
            version = None
            for version_attr in ['__version__', 'version', 'VERSION']:
                if hasattr(module, version_attr):
                    version = getattr(module, version_attr)
                    if callable(version):
                        version = version()
                    version = str(version)
                    break
            
            # Try alternative version detection for packages without standard version attributes
            if not version:
                version = self._get_package_version_alt(import_name)
            
            if self.debug:
                module_file = getattr(module, '__file__', 'built-in')
                self.logger.debug(f"Successfully imported {import_name} from: {module_file}")
                if version:
                    self.logger.debug(f"Version detected: {version}")
            
            return True, version, None
            
        except ImportError as e:
            if self.debug:
                self.logger.debug(f"ImportError for {import_name}: {str(e)}")
                # Try to get more detailed information about why import failed
                spec = importlib.util.find_spec(import_name)
                if spec is None:
                    self.logger.debug(f"Module spec not found for {import_name}")
                else:
                    self.logger.debug(f"Module spec found but import failed: {spec}")
            
            return False, None, str(e)
        except Exception as e:
            if self.debug:
                self.logger.debug(f"Unexpected error importing {import_name}: {str(e)}")
            return False, None, f"Unexpected error: {str(e)}"
    
    def _validate_dependency(self, dep: DependencyInfo) -> ValidationReport:
        """Validate a single dependency"""
        if self.debug:
            self.logger.debug(f"Validating dependency: {dep.name}")
        
        # Check if we should validate this dependency
        if not self._should_check_dependency(dep):
            if self.debug:
                self.logger.debug(f"Skipping {dep.name} - not required for current platform")
            return ValidationReport(
                name=dep.name,
                dependency_info=dep,
                result=ValidationResult.SUCCESS,
                available=False,
                error_message="Not required for current platform"
            )
        
        # Attempt to import the dependency
        available, version, error_message = self._check_import(dep.import_name)
        
        # Determine validation result
        if available:
            result = ValidationResult.SUCCESS
            install_command = None
        else:
            if dep.dependency_type == DependencyType.REQUIRED:
                result = ValidationResult.FATAL
            elif dep.dependency_type == DependencyType.PLATFORM_SPECIFIC:
                if self.platform_info['is_raspberry_pi'] and dep.platforms == ["raspberry_pi"]:
                    result = ValidationResult.ERROR
                else:
                    result = ValidationResult.WARNING
            else:
                result = ValidationResult.WARNING
            
            install_command = dep.install_hint
        
        report = ValidationReport(
            name=dep.name,
            dependency_info=dep,
            result=result,
            available=available,
            version=version,
            error_message=error_message,
            install_command=install_command
        )
        
        if self.debug:
            self.logger.debug(f"Dependency {dep.name}: {result.name} - Available: {available}")
            if version:
                self.logger.debug(f"Version: {version}")
            if error_message:
                self.logger.debug(f"Error: {error_message}")
        
        return report
    
    def validate_all(self) -> List[ValidationReport]:
        """Validate all dependencies and return reports"""
        self.logger.info("Starting dependency validation...")
        
        if self.debug:
            self.logger.debug(f"Platform: {self.platform_info['system']} {self.platform_info['machine']}")
            self.logger.debug(f"Python: {self.platform_info['python_version']}")
            self.logger.debug(f"Raspberry Pi: {self.platform_info['is_raspberry_pi']}")
            self.logger.debug(f"Development: {self.platform_info['is_development']}")
        
        self.reports = []
        
        for dep in self.dependencies:
            report = self._validate_dependency(dep)
            self.reports.append(report)
        
        return self.reports
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary statistics"""
        if not self.reports:
            return {}
        
        # Filter out skipped dependencies for cleaner summary
        checked_reports = [r for r in self.reports if not (r.result == ValidationResult.SUCCESS and not r.available)]
        
        summary = {
            'total_checked': len(checked_reports),
            'available': sum(1 for r in checked_reports if r.available),
            'missing': sum(1 for r in checked_reports if not r.available),
            'fatal_errors': sum(1 for r in self.reports if r.result == ValidationResult.FATAL),
            'errors': sum(1 for r in self.reports if r.result == ValidationResult.ERROR),
            'warnings': sum(1 for r in self.reports if r.result == ValidationResult.WARNING),
            'success': sum(1 for r in self.reports if r.result == ValidationResult.SUCCESS and r.available),
            'skipped': sum(1 for r in self.reports if r.result == ValidationResult.SUCCESS and not r.available),
            'can_start': sum(1 for r in self.reports if r.result == ValidationResult.FATAL) == 0
        }
        
        return summary
    
    def print_report(self, show_successful: bool = None) -> None:
        """Print detailed dependency report"""
        if show_successful is None:
            show_successful = self.debug
        
        print("\n" + "="*70)
        print("OBDII Display Application - Dependency Validation Report")
        print("="*70)
        
        # Platform information
        print(f"Platform: {self.platform_info['system']} {self.platform_info['machine']}")
        print(f"Python: {self.platform_info['python_version']}")
        print(f"Raspberry Pi: {'Yes' if self.platform_info['is_raspberry_pi'] else 'No'}")
        print(f"Development Mode: {'Yes' if self.platform_info['is_development'] else 'No'}")
        print()
        
        # Group reports by result type
        fatal_reports = [r for r in self.reports if r.result == ValidationResult.FATAL]
        error_reports = [r for r in self.reports if r.result == ValidationResult.ERROR]
        warning_reports = [r for r in self.reports if r.result == ValidationResult.WARNING]
        success_reports = [r for r in self.reports if r.result == ValidationResult.SUCCESS and r.available]
        skipped_reports = [r for r in self.reports if r.result == ValidationResult.SUCCESS and not r.available]
        
        # Print fatal errors
        if fatal_reports:
            print("❌ FATAL ERRORS (Application cannot start):")
            for report in fatal_reports:
                print(f"  • {report.name}: {report.error_message}")
                if report.install_command:
                    print(f"    Install: {report.install_command}")
                if report.dependency_info.description:
                    print(f"    Purpose: {report.dependency_info.description}")
                print()
        
        # Print errors
        if error_reports:
            print("🟡 ERRORS (Reduced functionality):")
            for report in error_reports:
                print(f"  • {report.name}: {report.error_message}")
                if report.install_command:
                    print(f"    Install: {report.install_command}")
                if report.dependency_info.description:
                    print(f"    Purpose: {report.dependency_info.description}")
                print()
        
        # Print warnings
        if warning_reports:
            print("⚠️  WARNINGS (Optional features unavailable):")
            for report in warning_reports:
                print(f"  • {report.name}: {report.error_message}")
                if report.install_command:
                    print(f"    Install: {report.install_command}")
                if report.dependency_info.description:
                    print(f"    Purpose: {report.dependency_info.description}")
                print()
        
        # Print successful dependencies
        if show_successful and success_reports:
            print("✅ AVAILABLE DEPENDENCIES:")
            for report in success_reports:
                version_str = f" (v{report.version})" if report.version else ""
                print(f"  • {report.name}{version_str}")
                if self.debug and report.dependency_info.description:
                    print(f"    Purpose: {report.dependency_info.description}")
            print()
        
        # Print skipped dependencies in debug mode
        if self.debug and skipped_reports:
            print("⏭️  SKIPPED DEPENDENCIES (Not required for current platform):")
            for report in skipped_reports:
                print(f"  • {report.name}: {report.error_message}")
                if report.dependency_info.description:
                    print(f"    Purpose: {report.dependency_info.description}")
            print()
        
        # Print summary
        summary = self.get_summary()
        print("📊 SUMMARY:")
        print(f"  Total Dependencies Checked: {summary['total_checked']}")
        print(f"  Available: {summary['available']}")
        print(f"  Missing: {summary['missing']}")
        print(f"  Fatal Errors: {summary['fatal_errors']}")
        print(f"  Errors: {summary['errors']}")
        print(f"  Warnings: {summary['warnings']}")
        if self.debug and summary.get('skipped', 0) > 0:
            print(f"  Skipped (Platform-specific): {summary['skipped']}")
        print()
        
        # Final status
        if summary['can_start']:
            print("✅ Application can start (all critical dependencies available)")
        else:
            print("❌ Application cannot start (missing critical dependencies)")
        
        print("="*70)
    
    def get_install_commands(self) -> List[str]:
        """Get installation commands for missing dependencies"""
        commands = []
        
        for report in self.reports:
            if not report.available and report.install_command:
                commands.append(report.install_command)
        
        return list(set(commands))  # Remove duplicates
    
    def can_start_application(self) -> bool:
        """Check if application can start (no fatal dependency errors)"""
        return all(report.result != ValidationResult.FATAL for report in self.reports)
    
    def _detect_virtual_environment(self) -> Dict[str, Any]:
        """Detect if we're running in a virtual environment and get details"""
        venv_info = {
            'in_venv': False,
            'venv_path': None,
            'venv_type': None,
            'base_prefix': getattr(sys, 'base_prefix', sys.prefix),
            'real_prefix': getattr(sys, 'real_prefix', None)
        }
        
        # Check various virtual environment indicators
        if hasattr(sys, 'real_prefix'):
            # virtualenv
            venv_info['in_venv'] = True
            venv_info['venv_type'] = 'virtualenv'
            venv_info['venv_path'] = sys.prefix
        elif sys.base_prefix != sys.prefix:
            # venv (Python 3.3+)
            venv_info['in_venv'] = True
            venv_info['venv_type'] = 'venv'
            venv_info['venv_path'] = sys.prefix
        elif os.environ.get('VIRTUAL_ENV'):
            # Environment variable set
            venv_info['in_venv'] = True
            venv_info['venv_type'] = 'env_var'
            venv_info['venv_path'] = os.environ['VIRTUAL_ENV']
        elif os.environ.get('CONDA_DEFAULT_ENV'):
            # Conda environment
            venv_info['in_venv'] = True
            venv_info['venv_type'] = 'conda'
            venv_info['venv_path'] = os.environ.get('CONDA_PREFIX', sys.prefix)
        
        return venv_info
    
    def _get_package_version_alt(self, import_name: str) -> Optional[str]:
        """Alternative method to get package version using pkg_resources or importlib.metadata"""
        # Map import names to package names for version detection
        import_to_package = {
            'yaml': 'PyYAML',
            'serial': 'pyserial',
            'bluetooth': 'pybluez',
            'pygame': 'pygame',
            # Add more mappings as needed
        }
        
        package_name = import_to_package.get(import_name, import_name)
        
        # Try importlib.metadata (Python 3.8+)
        try:
            if sys.version_info >= (3, 8):
                import importlib.metadata
                return importlib.metadata.version(package_name)
        except (ImportError, Exception):
            pass
        
        # Try pkg_resources (fallback)
        try:
            import pkg_resources
            return pkg_resources.get_distribution(package_name).version
        except (ImportError, Exception):
            pass
        
        # Try pip show command as last resort
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', package_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        return line.split(':', 1)[1].strip()
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass
        
        return None


def validate_dependencies(debug: bool = False) -> DependencyValidator:
    """Validate all dependencies and return validator instance
    
    Args:
        debug: Enable debug logging and detailed reporting
    
    Returns:
        DependencyValidator instance with validation results
    """
    validator = DependencyValidator(debug=debug)
    validator.validate_all()
    return validator


def main():
    """Main function for standalone dependency checking"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OBDII Display Application - Dependency Validator")
    parser.add_argument('--debug', action='store_true', help='Enable debug logging and detailed reporting')
    parser.add_argument('--show-successful', action='store_true', help='Show successful dependencies in report')
    parser.add_argument('--install-commands', action='store_true', help='Show installation commands for missing dependencies')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run validation
    validator = validate_dependencies(debug=args.debug)
    
    # Print report
    validator.print_report(show_successful=args.show_successful)
    
    # Show install commands if requested
    if args.install_commands:
        commands = validator.get_install_commands()
        if commands:
            print("\n📦 INSTALLATION COMMANDS:")
            for cmd in commands:
                print(f"  {cmd}")
            print()
    
    # Exit with appropriate code
    sys.exit(0 if validator.can_start_application() else 1)


if __name__ == "__main__":
    main()