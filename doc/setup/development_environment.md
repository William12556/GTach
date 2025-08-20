# Development Environment Setup

**Created**: 2025 08 20

## Prerequisites
- Python 3.9+
- Git version control
- 4GB RAM minimum
- Network connectivity

## Installation

### 1. Clone Repository
```bash
git clone [repository-url] GTach
cd GTach
```

### 2. Python Environment
```bash
# Verify Python version
python3 --version  # Should show 3.9+

# Install dependencies
pip3 install -r requirements.txt

# Development installation
python3 setup.py develop
```

### 3. Configuration
```bash
# Platform auto-detection creates development config
python3 -c "from src.gtach.utils.platform import get_platform_info; print(get_platform_info())"
```

## Verification

### Run Tests
```bash
python3 -m pytest src/tests/ -v
# Should show: 143 tests passed
```

### Start Application
```bash
# Debug mode with display simulation
python3 -m gtach.main --debug --simulate-display

# Check help
python3 -m gtach.main --help
```

## Development Workflow

### Code Changes
1. Make changes in `src/` directory
2. Run relevant tests: `python3 -m pytest src/tests/test_module.py`
3. Run full test suite before commits
4. Use debug logging: `--debug` flag

### Cross-Platform Testing
- Development machine: All tests with mocks
- Raspberry Pi: Hardware integration tests
- See [Testing Guide](../testing/testing_overview.md)

## IDE Configuration

### Recommended Settings
- Python interpreter: Project virtual environment
- Code formatting: Follow PEP 8
- Import organization: Group by standard/third-party/local

### Debugging
- Use `--debug` flag for verbose logging
- Log files in `logs/session_*.log`
- Mock display for GUI testing

## Project Structure
```
src/
├── gtach/           # Main application
├── tests/           # Test suite
└── provisioning/    # Deployment tools

doc/
├── protocol/        # Development standards
├── design/          # Architecture docs
└── setup/           # Setup guides
```

## Next Steps
- [Testing Overview](../testing/testing_overview.md)
- [Cross-Platform Guide](../development/cross_platform_guide.md)
- [Protocol Overview](../protocol/README.md)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | Verify `requirements.txt` installation |
| Test failures | Check Python version 3.9+ |
| Permission errors | Use virtual environment |
| Mock display issues | Install display simulation dependencies |

---

**Copyright**: Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
