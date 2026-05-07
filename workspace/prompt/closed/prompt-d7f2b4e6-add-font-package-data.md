Created: 2026 May 06

# Prompt: Add Font Package Data to pyproject.toml

---

```yaml
prompt_info:
  id: "prompt-d7f2b4e6"
  task_type: "code_generation"
  source_ref: "change-d7f2b4e6"
  date: "2026-05-06"
  iteration: 1
  coupled_docs:
    change_ref: "change-d7f2b4e6"
    change_iteration: 1
```

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Task: add font package-data to pyproject.toml so Michroma-Regular.ttf is
  included in the built wheel (d7f2b4e6).

  FILE: pyproject.toml

  Locate the section:
    [tool.setuptools.packages.find]
    where = ["src"]

  Immediately AFTER that section, INSERT:
    [tool.setuptools.package-data]
    "gtach" = ["assets/fonts/*.ttf", "assets/fonts/*.otf"]

  Do not modify any other section or file.

  VERIFY:
    python -c "import tomllib; d=tomllib.loads(open('pyproject.toml').read()); print(d['tool']['setuptools']['package-data'])"
    # Expected: {'gtach': ['assets/fonts/*.ttf', 'assets/fonts/*.otf']}
    # (Use tomllib on Python 3.11+; on 3.9 use: pip show tomli && python -c "import tomli...")
    # Alternatively verify with: grep -A2 'package-data' pyproject.toml
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial prompt |

---

Copyright (c) 2026 William Watson. MIT License.
