Created: 2026 May 06

# Change: Add Michroma Font to pyproject.toml Package Data

---

```yaml
change_info:
  id: "change-d7f2b4e6"
  title: "Add package_data entry for TTF fonts to pyproject.toml"
  date: "2026-05-06"
  author: "William Watson"
  status: "approved"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-d7f2b4e6"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-d7f2b4e6-michroma-font-missing-from-wheel.md"
  description: >
    Michroma-Regular.ttf absent from installed wheel on Pi because pyproject.toml
    has no package-data declaration for assets/fonts/.

scope:
  summary: "Add [tool.setuptools.package-data] stanza to pyproject.toml"
  affected_components:
    - name: "pyproject.toml"
      file_path: "pyproject.toml"
      change_type: "modify"
  out_of_scope:
    - "Font file itself (already present in source tree)"
    - "Any Python source files"

rational:
  problem_statement: "setuptools excludes non-Python files from wheel unless declared."
  proposed_solution: >
    Add to pyproject.toml:
      [tool.setuptools.package-data]
      "gtach" = ["assets/fonts/*.ttf", "assets/fonts/*.otf"]
  benefits:
    - "Michroma-Regular.ttf included in wheel; available on Pi after install"
    - "Forward-compatible: any future TTF/OTF font files auto-included"
  risks:
    - risk: "Slight wheel size increase"
      mitigation: "Font file is ~50KB; negligible"

technical_details:
  current_behavior: "dist/*.whl contains no files under gtach/assets/fonts/"
  proposed_behavior: "dist/*.whl contains gtach/assets/fonts/Michroma-Regular.ttf"
  implementation_approach: "Single stanza addition to pyproject.toml"
  code_changes:
    - component: "pyproject.toml"
      file: "pyproject.toml"
      change_summary: >
        Insert after [tool.setuptools.packages.find] section:

        [tool.setuptools.package-data]
        "gtach" = ["assets/fonts/*.ttf", "assets/fonts/*.otf"]
      functions_affected: []
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial change document |

---

Copyright (c) 2026 William Watson. MIT License.
