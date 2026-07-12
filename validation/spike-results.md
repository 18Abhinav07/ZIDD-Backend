# Spike Results - 2026-07-12

## Assumption 1: Existing report fields support stable skills and history

- File: `validation/spike-1-career-taxonomy.py`
- Result: PASS
- Evidence: Two paraphrased GD gaps mapped to one stable `gd_test:floor_management` identity, while report rows retained session, task, validity, and score fields.
- Impact: A closed Career taxonomy can replace prose hashes without another model call.

## Assumption 2: Memory can be scoped by mode and validity

- File: `validation/spike-2-memory-scope.py`
- Result: PASS
- Evidence: Existing memory rows retained `task_type`; a mode/validity filter isolated Interview evidence and excluded an invalid GD report.
- Impact: Cross-mode and invalid-report contamination can be fixed inside the current memory projection.

## Assumption 3: Existing persistence supports history, reports, and resume

- File: `validation/spike-3-history-endpoints.py`
- Result: PASS
- Evidence: The learning graph exposes report and prep-event session IDs, the report endpoint is async and available, and `PgStore` already supports latest active runtime lookup by module.
- Impact: The continuity UI does not require a second persistence system.

## Gate Decision

ALL PASS. The V2 architecture is empirically viable using existing report, event, and runtime seams.
