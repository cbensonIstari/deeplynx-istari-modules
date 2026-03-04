# Check Thermal Compliance — AI Context

## Quick Reference

- **DeepLynx local URL:** http://localhost:5000
- **Organization ID:** 1
- **Project ID:** 2 (Recon Drone MK-IV)
- **Data Source ID:** 2
- **Sample data:** 62 records, 83 edges, 16 classes, 15 relationships, 6 tags

## Key Record IDs

| Record | ID | Class |
|--------|----|-------|
| Propulsion subsystem | ~17 | Subsystem |
| Power System subsystem | ~18 | Subsystem |
| T-Motor U8 II KV150 | ~25 | Component |
| Main Battery Pack | ~26 | Component |

## How to Run

```bash
cd use-cases/check-thermal-compliance
python check_thermal_compliance.py
```

Output goes to `output/` directory.

## Gotchas

- DeepLynx `properties` field is a JSON **string** in API responses — must `json.loads()` it
- Record creation requires `original_id` field (unique per data source)
- Edge creation supports `relationship_name` (string) as alternative to `relationship_id` (int)
- Tags can be passed as string names in the `tags` field of CreateRecordRequestDto
- Graph API max depth is 3
- Class/relationship/tag routes are project-scoped (`/projects/{id}/...`), not org-scoped
