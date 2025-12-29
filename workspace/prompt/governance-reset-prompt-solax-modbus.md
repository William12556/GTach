# Governance Reset Prompt for solax-modbus

## Objective

Reset the project `/Users/williamwatson/Documents/GitHub/solax-modbus` to achieve strict compliance with governance.md from `/Users/williamwatson/Documents/GitHub/LLM-Governance-and-Orchestration/ai/governance.md`.

---

## Reference: What Was Done to Reset GTach

### Phase 1: Analysis

Compared project structure against governance.md P01.2.6 required structure:

```
└── <project name>/
    ├── ai/                       # Operational rules
    │   └── governance.md
    ├── venv/                     # (excluded from git)
    ├── dist/                     # (excluded from git)
    ├── workspace/                # Execution space
    │   ├── admin/                # (excluded from git)
    │   ├── requirements/
    │   │   └── closed/
    │   ├── design/
    │   ├── change/
    │   │   └── closed/
    │   ├── knowledge/
    │   ├── issues/
    │   │   └── closed/
    │   ├── proposal/             # (excluded from git)
    │   │   └── closed/
    │   ├── prompt/
    │   │   └── closed/
    │   ├── trace/
    │   ├── audit/
    │   │   └── closed/
    │   ├── test/
    │   │   ├── closed/
    │   │   └── result/
    │   │       └── closed/
    │   └── ai/                   # (excluded from git)
    ├── docs/                     # Technical Documents
    ├── tests/                    # Test files (root level)
    ├── src/                      # Source code
    └── deprecated/               # Archive (excluded from git)
```

### Phase 2: Created ai/ Folder Structure

Per P00 1.1.17, copied from LLM-Governance-and-Orchestration:
- `ai/governance.md`
- `ai/instructions.md`
- `ai/obsidian_markdown_guidelines.md`
- `ai/templates/T01-design.md` through `T07-requirements.md`

### Phase 3: Created Complete workspace/ Hierarchy

Created all folders with README.md files:
- `workspace/admin/`
- `workspace/requirements/` and `closed/`
- `workspace/design/`
- `workspace/change/` and `closed/`
- `workspace/knowledge/`
- `workspace/issues/` and `closed/`
- `workspace/proposal/` and `closed/`
- `workspace/prompt/` and `closed/`
- `workspace/trace/`
- `workspace/audit/` and `closed/`
- `workspace/test/`, `closed/`, `result/`, `result/closed/`
- `workspace/ai/`

Created traceability matrix skeleton: `workspace/trace/trace-0000-master_traceability-matrix.md`

### Phase 4: Created docs/ and tests/ Folders

With README.md files per P01.2.3.

### Phase 5: Archived Non-Compliant Items to deprecated/

Folders archived:
- `cache/`, `config/`, `data/`, `htmlcov/`, `logs/`, `packages/`, `releases/`

Files archived:
- `.gtach-version`, `Makefile`, `requirements.txt`, `.coverage`

### Phase 6: Updated .gitignore

Per P01.2.2:
```
.DS_Store
**/.DS_Store
.obsidian/
*.log
**/*.log
**/logs
.zsh_history
coverage.xml
.coverage
htmlcov/
test.txt
**/tmp
deprecated/
workspace/admin/
workspace/ai/
workspace/proposal/
workspace/proposal/closed/
venv/
.venv/
*.pyc
__pycache__/
.pytest_cache/
dist/
build/
*.egg-info/
.mypy_cache/
```

---

## Instructions for solax-modbus Reset

### Current solax-modbus Structure (Non-Compliant Items)

| Item | Issue |
|------|-------|
| `governance/` folder | Should be `ai/` per P01.2.6 |
| `governance/governance.md` | Should be `ai/governance.md` |
| Missing `ai/templates/` | Required per P00 1.1.17 |
| Missing `ai/instructions.md` | Copy from LLM-Governance-and-Orchestration |
| Missing `ai/obsidian_markdown_guidelines.md` | Copy from LLM-Governance-and-Orchestration |
| `.framework-ref` | Non-compliant file, archive to deprecated/ |
| `requirements.txt` | Superseded by pyproject.toml per P01.2.8 |
| Missing `pyproject.toml` | Required per P01.2.8 |
| Missing `tests/` folder | Required per P01.2.6 |
| Missing workspace folders | `admin/`, `requirements/`, `knowledge/`, `proposal/`, `prompt/`, `audit/`, `ai/` |
| Missing closed/ subfolders | In change/, issues/, test/ |
| Incomplete .gitignore | Missing entries per P01.2.2 |

### Step-by-Step Reset Procedure

**1. Archive governance/ folder to deprecated/**
```
Move governance/ → deprecated/governance_old/
```

**2. Create new ai/ folder structure**
```
Create ai/
Copy from /Users/williamwatson/Documents/GitHub/LLM-Governance-and-Orchestration/ai/:
  - governance.md
  - instructions.md
  - obsidian_markdown_guidelines.md
  - templates/ (entire folder with T01-T07)
```

**3. Archive non-compliant root files**
```
Move to deprecated/:
  - .framework-ref
  - requirements.txt
```

**4. Create missing workspace/ folders**
```
Create with README.md:
  - workspace/admin/
  - workspace/requirements/ and closed/
  - workspace/knowledge/
  - workspace/proposal/ and closed/
  - workspace/prompt/ and closed/
  - workspace/audit/ and closed/
  - workspace/ai/
  - workspace/change/closed/
  - workspace/issues/closed/
  - workspace/test/closed/
  - workspace/test/result/
  - workspace/test/result/closed/
```

**5. Create traceability matrix skeleton**
```
Create workspace/trace/trace-0000-master_traceability-matrix.md
```

**6. Create tests/ folder**
```
Create tests/README.md
```

**7. Create pyproject.toml**
Per P01.2.8 template in governance.md.

**8. Update .gitignore**
Replace with P01.2.2 compliant version.

**9. Update deprecated/README.md**
Document all archived items.

---

## Execution Command

Start a new conversation and paste this prompt:

```
Read governance.md from /Users/williamwatson/Documents/GitHub/LLM-Governance-and-Orchestration/ai/governance.md

Reset the project /Users/williamwatson/Documents/GitHub/solax-modbus to achieve strict compliance with governance.md P01.2.6.

Follow the step-by-step procedure:
1. Archive governance/ folder to deprecated/governance_old/
2. Create new ai/ folder with governance.md, instructions.md, obsidian_markdown_guidelines.md, and templates/ from LLM-Governance-and-Orchestration
3. Archive .framework-ref and requirements.txt to deprecated/
4. Create missing workspace folders with README.md files and closed/ subfolders
5. Create traceability matrix skeleton in workspace/trace/
6. Create tests/ folder with README.md
7. Create pyproject.toml per P01.2.8
8. Update .gitignore per P01.2.2
9. Update deprecated/README.md with inventory of archived items

Preserve: src/, docs/ (contains PDF reference documents), LICENSE, README.md
```

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
