---
name: tdd
description: Implement features using Test-Driven Development (TDD) with Red-Green-Refactor cycle.
disable-model-invocation: true
---

# Test-Driven Development

Implement $ARGUMENTS using Test-Driven Development (TDD).

## TDD Cycle (Role Split)

- **Codex**: Write tests and implementation
- **Claude Code**: Organize test suites and run tests
- **Codex**: Analyze failures and propose fixes

```
Repeat: Red → Green → Refactor

1. Red:    Codex writes a failing test
2. Green:  Codex writes minimal code to pass the test
3. Refactor: Codex refactors code (tests still pass)
```

## Implementation Steps

### Phase 1: Test Design (Claude)

1. **Confirm Requirements**
   - What is the input
   - What is the output
   - What are the edge cases

2. **List Test Cases**
   ```
   - [ ] Happy path: Basic functionality
   - [ ] Happy path: Boundary values
   - [ ] Error case: Invalid input
   - [ ] Error case: Error handling
   ```

### Phase 2: Red-Green-Refactor (Codex + Claude)

#### Step 1: Write First Test (Red) — Codex

```python
# tests/test_{module}.py
def test_{function}_basic():
    """Test the most basic case"""
    result = function(input)
    assert result == expected
```

Claude runs test and **confirms failure**:
```bash
uv run pytest tests\\test_{module}.py -v
```

#### Step 2: Implementation (Green) — Codex

Write **minimal** code to pass the test:
- Don't aim for perfection
- Hardcoding is OK
- Just make the test pass

Claude runs test and **confirms success**:
```bash
uv run pytest tests\\test_{module}.py -v
```

#### Step 3: Refactoring (Refactor) — Codex

Improve while tests still pass:
- Remove duplication
- Improve naming
- Clean up structure

Claude runs tests to confirm:
```bash
uv run pytest tests\\test_{module}.py -v  # Confirm still passes
```

#### Step 4: Next Test

Return to Step 1 with next test case from the list.

### Phase 3: Completion Check (Claude)

```bash
# Run all tests
uv run pytest -v

# Check coverage (target 80%+)
uv run pytest --cov={module} --cov-report=term-missing
```

## Report Format

```markdown
## TDD Complete: {Feature Name}

### Test Cases
- [x] {test1}: {description}
- [x] {test2}: {description}
...

### Coverage
{Coverage report}

### Implementation Files
- `src/{module}.py`: {description}
- `tests/test_{module}.py`: {N} tests
```

## Notes

- Delegate test authoring to Codex; Claude runs and organizes
- Keep each cycle **small**
- Refactor **after** tests pass
- Prioritize **working code** over perfection
