# Status log: 2026-10-06

## RFI and Requests consolidation (one PR, branch `claude/trusting-planck-lpx0oa`)

Spec: `tasks/2026-10-06-rfi-requests-consolidation.md`. Built on `main` at `9cf6977`. Open for review, not merged.

- **WP-A RFI sub-view and link picker.** Client links tab groups items into Not yet sent and a covered disclosure that names the covering contact and expiry (`coverage_labels`). The contact and limits block stays hidden until an item is checked (`syncRfiLinkForm` in `app.js`). Validation errors keep the selection and typed values. Generate redirects to `?tab=versions`, issue to `?tab=links`. The RFI page has an All requests back link; Evidence "Ask the client" opens the Client links tab.
- **WP-B Requests hub.** Each assessment row has a Next step link to the right RFI tab. Link cards come first; the free-text form moves into a collapsed Request something else disclosure that reopens on an error.
- **WP-C Retention to Settings.** Settings > Data housekeeping gains an Archive and purge card listing every active, closed and archived engagement (archived last). Both Overviews lose the Retention section; the engagement header loses its archive actions; archived banners link to Settings. Archive and unarchive accept `return_to=/settings`. `partials/engagement_retention.html` is deleted.
- **WP-D Scope readability.** Ruled Required and Recommended groups with counts; line-list excluded and proposed lists.
- **WP-E.** `RFI_REQUESTS_PATHS` allowance added to `tests/yozora_paths.py` and the enumerating guards; migration map and design-system docs updated.

Pixel gates for `b6-rfi`, `b6-magic_links`, `b3-scope-complete`, `engagement_detail` and `b1-firm_settings` diverge on purpose and wait for Saqlain's human gate.
