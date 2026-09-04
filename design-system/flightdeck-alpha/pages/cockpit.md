# Cockpit page overrides (override MASTER.md)

The Cockpit (and the whole app) is an autonomous options trading desk.
Dark mode is mandatory: judges demo it on stage, operators watch it for
hours, and a light dashboard looks wrong next to a live market terminal.
The MASTER palette is a light "analytics dashboard" default — we override
it here.

## Palette (dark trading desk)

| Role | Hex | CSS variable | Token |
|------|-----|--------------|-------|
| Background base | `#0B1020` | `--bg` | `bg.base` |
| Background raised | `#121A2F` | `--bg-raised` | `bg.raised` |
| Background soft | `#18233D` | `--bg-soft` | `bg.soft` |
| Surface (glass) | `rgba(18,26,47,0.78)` | `--surface` | `surface.glass` |
| Border | `#2A3554` | `--border` | `border.default` |
| Border strong | `#3A466B` | `--border-strong` | `border.strong` |
| Text primary | `#E8EEFC` | `--text` | `text.primary` |
| Text muted | `#9AA8C7` | `--muted` | `text.muted` |
| Text faint | `#6E7A99` | `--muted-2` | `text.faint` |
| Accent cyan | `#4CC9F0` | `--accent` | `accent.cyan` |
| Accent violet | `#7B61FF` | `--accent-2` | `accent.violet` |
| Status ok | `#3DD68C` | `--ok` | `status.ok` |
| Status warn | `#F4B942` | `--warn` | `status.warn` |
| Status danger | `#FF6B6B` | `--danger` | `status.danger` |
| Status info | `#4CC9F0` | `--info` | `status.info` |
| P&L positive | `#3DD68C` | `--pos` | `pnl.positive` |
| P&L negative | `#FF6B6B` | `--neg` | `pnl.negative` |

## Typography

- Display + headings: `Inter` (system fallback). Inter reads better for
  short uppercase labels than Fira Code.
- Body: `Inter`, 14px / 1.5.
- Numerics: `JetBrains Mono`, tabular-nums for currency and counts. Loaded
  from Google Fonts with `font-display: swap` so first paint never blocks.
- All numeric cells use `font-variant-numeric: tabular-nums`.

## Layout grid

- Container max-width: 1440px (was 1280px). Centered.
- Topbar: floating, `top: 16px`, full width with 16px gutters.
- Sidebar nav: vertical on >= 1024px, horizontal scroll strip on < 1024px.
- Cockpit grid: 12 columns at >= 1024px, single column at < 1024px.
- Card grid gap: 16px. Card padding: 20px.

## Density rules

- Table row height: 44px.
- KPI tile height: 112px.
- Monospace cells: 13px.
- Section titles: 11px uppercase tracking 0.08em, muted color.

## Effects

- Hover: background recolor + 1px border accent, **no scale** (avoids
  layout shift in dense tables).
- Focus: 2px cyan ring offset 2px, visible on every interactive element.
- Loading: 1.2s linear spinner, accessible label.
- Status pulse: 2s pulse animation for live indicators, **suppressed**
  when `prefers-reduced-motion: reduce`.

## Forbidden on Cockpit (and entire app)

- No emoji icons. Use Lucide React SVG icons, 16px and 20px sizes only.
- No `border-white/10` (invisible in dark on OLED). Use the token border.
- No `bg-white` accents on dark glass. Use the token surface.
- No hardcoded hex strings inside components. Use tokens via CSS variables
  in `index.css`.
