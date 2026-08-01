# Experiments

This directory stores experiment configuration and memo outputs.

## Planned Files

| file/path | purpose |
|---|---|
| `case_registry.yml` | canonical list of cases, route, validation level, weather/soil/crop sources |
| `scenario_config.yml` | irrigation strategies and constraints |
| `uncertainty_config.yml` | weather/soil/management perturbation definitions |
| `tool_trace_schema.json` | required fields for tool-call provenance |
| `memos/` | generated action memos |

## Case Status Values

Use one of:

- `validated`: observed or literature benchmark exists and tolerance is met.
- `benchmark_reproduced`: literature benchmark reproduced enough for method demonstration.
- `workflow_only`: useful for provenance and memo-faithfulness, not crop-model validation.

Korean candidate cases should start as `workflow_only` until forcing, soil, management, and validation targets are proven.

