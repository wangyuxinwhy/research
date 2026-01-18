# Evident - Project Guidelines

## Code Style

### Language
- All code, comments, and docstrings must be in English
- No Chinese or other languages in source files

### Comments & Docstrings
- Comments explain **Why** or **How**, never **What**
- No single-line obvious docstrings that repeat the name
- Only public APIs get docstrings, and only when they add real value
- If naming is clear enough, no docstring needed
- Delete useless comments - they are noise

### Naming
- Semantic, self-explanatory names
- Classes: nouns (`Experiment`, `AnalysisResult`)
- Methods: verbs (`analyze`, `sample`, `compute`)
- Booleans: `is_`/`has_` prefix
- Private: `_` prefix, no exceptions

### Type Annotations
- 100% type coverage required
- All function signatures must have type hints
- All class attributes must have type hints

## Python

### Version
- Python >= 3.14

### Tools
- Package manager: `uv`
- Linter & formatter: `ruff`
- Type checker: `basedpyright` (strict mode)

### Configuration

```toml
[tool.ruff]
target-version = "py314"
line-length = 88

[tool.ruff.lint]
select = ["ALL"]
ignore = ["D1", "ANN101", "ANN102"]

[tool.basedpyright]
pythonVersion = "3.14"
typeCheckingMode = "all"
```

## Rust

### Lints

```toml
[lints.rust]
unsafe_code = "forbid"

[lints.clippy]
all = "deny"
pedantic = "deny"
```

## Git

### Commit Messages
- Imperative mood: "Add feature" not "Added feature"
- Format: `<type>: <subject>` (feat, fix, refactor, docs, chore)
- One commit, one logical change
