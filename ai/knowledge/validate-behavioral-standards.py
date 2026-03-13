#!/usr/bin/env python3
"""
Behavioral Standards Validator

Validates behavioral-standards.yaml against its JSON schema.
Usage: ./validate-behavioral-standards.py [path-to-yaml] [path-to-schema]
"""

import sys
import json
import yaml
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("Error: jsonschema package required. Install via: pip install jsonschema")
    sys.exit(2)


def validate_behavioral_standards(yaml_path: Path, schema_path: Path) -> bool:
    """
    Validate YAML configuration against JSON schema.
    
    Args:
        yaml_path: Path to behavioral-standards.yaml
        schema_path: Path to behavioral-standards.schema.json
        
    Returns:
        True if valid, False otherwise
    """
    try:
        with open(yaml_path, 'r') as f:
            standards = yaml.safe_load(f)
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        jsonschema.validate(standards, schema)
        
        print(f"✓ Behavioral standards valid: {yaml_path}")
        return True
        
    except yaml.YAMLError as e:
        print(f"✗ YAML parsing error: {e}")
        return False
        
    except json.JSONDecodeError as e:
        print(f"✗ JSON schema parsing error: {e}")
        return False
        
    except jsonschema.ValidationError as e:
        print(f"✗ Validation failed:")
        print(f"  Path: {'.'.join(str(p) for p in e.path)}")
        print(f"  Message: {e.message}")
        return False
        
    except FileNotFoundError as e:
        print(f"✗ File not found: {e.filename}")
        return False
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent.parent
    
    if len(sys.argv) == 3:
        yaml_path = Path(sys.argv[1])
        schema_path = Path(sys.argv[2])
    elif len(sys.argv) == 1:
        yaml_path = script_dir / "behavioral-standards.yaml"
        schema_path = script_dir / "behavioral-standards.schema.json"
    else:
        print("Usage: validate-behavioral-standards.py [yaml-path] [schema-path]")
        print("       validate-behavioral-standards.py (uses default paths)")
        sys.exit(2)
    
    success = validate_behavioral_standards(yaml_path, schema_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
