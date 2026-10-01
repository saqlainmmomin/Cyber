Components b4 built without, using inline token styles or borrowed classes:

- File dropzone: dashed border, idle, drag-over and error variants. Used inline `border:1px dashed var(--line-strong)` on a div (documents_tab). Also needed on the client upload page.
- Progress bar: borrowed `.stp .rail i` for the upload bar. Needs a standalone `.progress-bar` with a determinate value and an indeterminate variant.
- Key-value grid (label above value): inline grid used in evidence_detail, evidence_reuse, workpaper_entry, aws_evidence. Needs `.kv`.
- Code block with copy button: `pre` styled inline inside `.cite` (aws_evidence policies). Needs `.code` with a header and copy action.
- Stat tile (label plus number): inline on `.glass` in workpaper. Needs `.stat`.
- Disclosure (details/summary): browser default summary used in desk_review and aws_evidence. Needs `.disclose` with chevron and focus ring.
- Select chevron: `.field select` has no arrow; a `chev-d` icon is placed after it by hand. Needs the arrow in `.field select` itself.
- Timeline list: revision history uses `.rows`. Fine for now; a connected rail would read better for long histories.
