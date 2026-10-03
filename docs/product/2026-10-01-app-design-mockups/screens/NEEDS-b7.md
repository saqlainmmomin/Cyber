# Needs from batch b7 (system)

Components missing from `yozora-components.css`. Each screen was built without them, using page-local layout rules where unavoidable (marked local below).

- Popover and dropdown menu: `.menu` only works as the bottom-anchored user menu (absolute, bottom:52px, 100% wide). Needs a general anchored variant (top or bottom, left or right aligned, fixed width, flip near the viewport edge) plus `.menu hr` separator, group heading (`.gh`), selected item with trailing check, danger item, `aria-disabled` item, and a `:focus-visible` ring on items. Used in b7-menus-popovers (local `.anchor`, `.menu hr`, `.mi`, `.gh`, `.pop-body`).
- Tooltip: no component. Icon-only buttons rely on `aria-label` only, which gives sighted mouse users no label.
- Date picker: input styling and calendar panel (single date and range). Needed for period and evidence cut-off fields in the new engagement flow. Not built here; `i-calendar` is in the b7 sprite.
- File dropzone: drop target with idle, drag-over, uploading and error states; client upload page needs 44px touch size. Not built here.
- Pagination: no component. b7-dark-dense uses a local `.pager` row with two ghost icon buttons and a count. Needs page links or numbered window, rows-per-page select, disabled ends.
- Toast variants and container: `.toast` has the success icon colour only. Needs error, information, action (Undo), dismiss button, and a fixed stack container (bottom-right desktop, full width above the safe area on phones). Local: `.toast.bad`, `.toast.info`, `.toasts`.
- Skeleton variants: `.skel` is a 12px line only. Needs block, circle (score ring), pill and chip shapes, and a visually hidden "Loading" label utility (`.sr-only`). Local: `.skel.circle`, `.skel.pill-s`, `.skel.chip-s`, `.skel.r`.
- HTMX transition utilities: `.htmx-swapping`, `.htmx-settling` and a 200 ms fade-in for the swapped target. Local `.swap-in` keyframe in b7-htmx-swaps.
- Button loading state: a busy variant with an inline spinner. The swap demo uses a disabled button with changed text instead.
- Modal behaviour: `.scrim-modal` is fixed only, so specimens override to absolute. Needs a bottom-sheet variant under 600px, a scroll-lock note, and a typed-confirmation pattern (field plus disabled destructive button) as a documented variant.
- `[hidden]` guard: `.empty`, `.scrim-modal`, `.toasts` and similar set `display` and so override the `hidden` attribute. Add `[hidden]{display:none!important}` to the shared CSS.
- Breadcrumb overflow: three crumbs overflow at 390px. Needs collapse of the middle items into an ellipsis menu.
- Touch sizing: client pages need a documented 44px control size. b7-link-expired sets `--h:44px` on `.btn` locally.
