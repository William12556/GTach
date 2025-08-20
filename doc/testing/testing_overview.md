# Testing Overview

**Created**: 2025 08 20

## Testing Architecture

### Four-Layer Strategy
1. **Unit Tests** (Mac Compatible) - Individual function validation
2. **Business Logic Tests** (Mac Compatible) - Component integration  
3. **Platform Interface Tests** (Mock Mac/Real Pi) - API validation
4. **Hardware Integration Tests** (Pi Only) - Hardware validation

## Running Tests

### Development Environment
```bash
# Full test suite
python3 -m pytest src/tests/ -v

# Specific test categories
python3 -m pytest src/tests/unit/ -v
python3 -m pytest src/tests/integration/ -v

# With coverage
python3 -m pytest src/tests/ --cov=src/gtach
```

### Raspberry Pi Environment
```bash
cd /opt/gtach
python3 -m pytest src/tests/ -v
```

## Test Categories

### Unit Tests
- Function-level validation
- Mock all dependencies
- 80%+ coverage requirement
- Mac development compatible

### Integration Tests  
- Component interaction testing
- Workflow validation
- Cross-platform behavior verification
- Business logic validation

### Hardware Tests (Pi Only)
- GPIO interface validation
- Display driver testing
- Touch interface verification
- System resource monitoring

## Test Configuration

### Mock Strategy
- Display simulation for development
- GPIO mocking for cross-platform
- Platform detection overrides
- Dependency injection patterns

### Performance Testing
- Frame rate validation (60 FPS target)
- Memory usage monitoring
- Touch response latency
- System resource utilization

## Adding Tests

### Test Structure
```python
import pytest
from unittest.mock import Mock, patch

class TestComponent:
    def test_functionality(self):
        # Arrange, Act, Assert pattern
        pass
```

### Naming Convention
- Test files: `test_[module].py`
- Test classes: `Test[Component]`
- Test methods: `test_[functionality]`

For detailed testing procedures, see [Testing Strategy](testing_strategy.md).

---

**Copyright**: Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
