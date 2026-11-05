---
description: Docstring, comment, and README standards. Use when writing documentation.
globs: "**/*.{py,md}"
alwaysApply: false
trigger: glob
paths:
  - "**/*.py"
  - "**/*.md"
---
# Documentation Standards

## Docstrings

- Google style.
- State concisely what a class or function does.
- List arguments, public attributes, return value, and raised exceptions with their types. Omit empty sections.
- List `@property` methods as attributes, typed by the getter's return type.
- Do not list methods, or protected and private attributes.
- Mark defaulted arguments as optional and state the default last: `arg (int, optional): Limit. Defaults to 10.`
- Put constructor arguments in `__init__`, not the class docstring.

```python
def example_function(param1: str, param2: int = 10) -> bool:
    """Brief description of what the function does.

    Args:
        param1 (str): Description of param1.
        param2 (int, optional): Description of param2. Defaults to 10.

    Returns:
        bool: Description of return value.

    Raises:
        ValueError: When param1 is invalid.
    """
```

## Comments

- Self-documenting code first. Comments explain why, not what.
- TODO and FIXME carry an issue number.
- Type hints replace comments about parameter types.

## READMEs

- Installation, usage with expected output, and every environment variable.
- Keep them current in the same PR that changes behavior.
