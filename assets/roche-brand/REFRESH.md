# Refreshing Roche Brand Asset Library

This bundle is a **point-in-time snapshot** of `branding.roche.com` and `fonts.roche.com`. Refresh quarterly or when brand guidelines change.

## When to refresh

- Quarterly cadence (next due: 2026-08-17)
- Notice from Roche communications about brand update
- Discrepancy spotted in PoC use (e.g. CDN URL pattern changed, like the May 2026 fonts.roche.com migration from `/fonts/` to `/fonts/{family}/latest/`)

## Prerequisites

1. Frontify session cookie at `~/.config/frontify/cookies.json` (mode 600). Get from your browser via DevTools → Application → Cookies → branding.roche.com → `frontify-session-id`.
2. Playwright + Chromium (already in `~/.cache/ms-playwright/`)

## Refresh procedure

### Fonts (no SSO, fast)

```bash
cd assets/roche-brand/fonts
for fam in roche-sans roche-serif noto-sans noto-serif; do
  for f in $fam/*.woff2; do
    base=$(basename "$f")
    curl -sL -o "$f" "https://fonts.roche.com/fonts/$fam/latest/$base"
  done
done
```

### Brand state + portal navigation + page contents

```bash
# Hub-level brand state (10 sec)
python3 demos/gslide-authoring/scripts/frontify_reader.py \
  --mode state https://branding.roche.com/hub/6 \
  --save ~/.cache/frontify-hub-6-state.json

# Portal API bundle (30 sec)
python3 demos/gslide-authoring/scripts/frontify_reader.py \
  --mode api https://branding.roche.com/hub/6 \
  --endpoints '/api/portal/6,/api/portal-navigation/6,/api/portal/6/appearance,/api/portal/6/font-families,/api/portal/6/font-styles' \
  --save ~/.cache/frontify-hub-6-api-bundle.json

# Brand Elements + Templates document pages (2-3 min)
# (custom script — not a single API call. See snapshots/page-index.json for page IDs.)
```

### Regenerate snapshots in this directory

After updating `~/.cache/*.json`, regenerate sanitized snapshots:

```bash
# (TODO: extract this into a reusable script under scripts/)
python3 -c "<see commit history for the snapshot generation logic>"
```

### Update _meta.json

```json
{
  "snapshot_date": "<new date>",
  "next_refresh_due": "<new date + 3 months>"
}
```

## Validation

After refresh, validate:

1. `tokens/colors.json` `primary.roche_blue.hex` is still `#0B41CD` (sanity check — if changed, brand has been updated and this is real news worth a comms thread)
2. `fonts/roche-sans/RocheSans-Regular.woff2` is non-zero, opens in `file` command
3. `snapshots/portal-navigation.json` includes Brand Elements (doc 26) and Templates (doc 29)
