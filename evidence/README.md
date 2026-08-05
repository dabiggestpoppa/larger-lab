# Evidence Repository

This repository contains evidence artifacts for the Capital Routing Research System.

## Purpose

The evidence repository provides the necessary validation data for Phase 1 readiness checks, including:

- Nautilus reproduction evidence (Book 2)
- Classification evidence (Book 3)  
- Independent approval (Approval)

## Structure

```
evidence/
├── .git              # Git submodule reference
├── README.md        # This file
├── book_2/          # Nautilus evidence
│   ├── run_001/    # Run 1 evidence
│   ├── run_002/    # Run 2 evidence
│   └── run_003/    # Run 3 evidence
├── book_3/          # Classification evidence
│   ├── classification.json
│   └── metadata.json
└── approval/        # Independent approval
    ├── approval.json
    └── metadata.json
```

## Usage

This evidence repository is used by the Reality Lock (Phase 1) to validate:

1. **Required artifacts exist** - All evidence files are present
2. **Artifact schemas are valid** - JSON schema validation passes
3. **Evidence repository SHA matches** - Git submodule integrity
4. **Book 2 contains Nautilus evidence** - Two-run reproduction
5. **Book 3 is evidence-based** - Classification validation
6. **No unresolved critical blockers** - Clean status
7. **Independent approval exists** - Explicit validation

## Status

✅ **READY FOR PHASE 1 VALIDATION**

The evidence repository provides the necessary validation data for the Capital Routing Research System to proceed to Phase 2.