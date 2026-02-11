---
name: "archive_task"
description: "Use when a task is complete and you need to move its PRD artifacts from INPROGRESS to ARCHIVE and finalize archival bookkeeping."
---

# ARCHIVE_TASK — Move Single Completed Task to Archive

**Version:** 1.0.0

## Inputs

| Variable | Description |
|----------|-------------|
| `TASK_ID` | Task identifier (e.g., `P1-T1`) |
| `TASK_NAME` | Task name in PascalCase (e.g., `Create_Project_Structure`) |
| `VERDICT` | One of: `PASS`, `FAIL`, `PARTIAL` |
| `DATE` | Archive date in `YYYY-MM-DD` format |

## Steps

```bash
# 1. Create task subfolder
scripts/archive_primitive.sh prepare-task "${TASK_ID}" "${TASK_NAME}" >/dev/null

# 2. Move PRD file
mv "SPECS/INPROGRESS/${TASK_ID}_${TASK_NAME}.md" \
   "SPECS/ARCHIVE/${TASK_ID}_${TASK_NAME}/"

# 3. Move validation report (if exists)
[ -f "SPECS/INPROGRESS/${TASK_ID}_Validation_Report.md" ] && \
mv "SPECS/INPROGRESS/${TASK_ID}_Validation_Report.md" \
   "SPECS/ARCHIVE/${TASK_ID}_${TASK_NAME}/"

# 4. Move any other task artifacts matching TASK_ID prefix
for f in SPECS/INPROGRESS/${TASK_ID}_*.md; do
  [ -f "$f" ] && mv "$f" "SPECS/ARCHIVE/${TASK_ID}_${TASK_NAME}/"
done

# 5. Append archive metadata to PRD
cat >> "SPECS/ARCHIVE/${TASK_ID}_${TASK_NAME}/${TASK_ID}_${TASK_NAME}.md" << EOF

---
**Archived:** ${DATE}
**Verdict:** ${VERDICT}
EOF

# 6. Update INDEX.md - add to Archived Tasks table
# Insert row: | ${TASK_ID} | [${TASK_ID}_${TASK_NAME}/](${TASK_ID}_${TASK_NAME}/) | ${DATE} | ${VERDICT} |

# 7. Update INDEX.md - add to Archive Log table
# Ensure the header separator stays directly under the header row:
# | Date | Task ID | Action |
# |------|---------|--------|
# If missing, restore it; do not insert the separator as a data row.
# Insert row: | ${DATE} | ${TASK_ID} | Archived ${TASK_NAME} (${VERDICT}) |

# 8. Update INDEX.md - set Last Updated date
# Set **Last Updated:** ${DATE}
```

## Postconditions

- `SPECS/ARCHIVE/${TASK_ID}_${TASK_NAME}/` exists with all task files
- PRD file contains archive metadata footer
- `SPECS/ARCHIVE/INDEX.md` updated with new entry
- `SPECS/INPROGRESS/` contains no files matching `${TASK_ID}_*`
