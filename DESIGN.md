Redesign the complete UI of this Clash Royale clan tracker web app (CrStats).
The app has three pages: Dashboard, Rankings, War.

## Design Direction
Dark theme. Dense, data-forward layout. Sharp edges — no rounded corners except 
where functionally necessary (max border-radius: 4px). This is a competitive gaming 
tool, not a SaaS dashboard.

## Color Palette (strict)
- Background: #0d0d0f
- Surface/Cards: #141418
- Border: #1e1e24
- Primary accent: #e8a020  (gold — matches Clash Royale branding)
- Danger/War accent: #c0392b
- Text primary: #f0f0f0
- Text secondary: #6b6b7a
- Positive/green: #27ae60

## Typography
- Font: "Rajdhani" (Google Fonts) for headings and stat numbers — geometric, 
  slightly condensed, gaming feel
- Font: "IBM Plex Mono" for data/numbers/tags
- NO Inter, NO Roboto, NO system-ui

## Layout Rules
- Navigation: left sidebar, 56px wide collapsed / 200px expanded. Dark, borderless.
- Cards: NO soft shadows. Use 1px solid border (#1e1e24) instead.
- Stat numbers: large (2.5–4rem), Rajdhani, gold or white.
- Tables: full-width, row hover with #1e1e24 background, no card wrapping.
- Progress bars: 3px height, sharp ends (border-radius: 0), colored per metric.
- Spacing: tight — 12px/16px gaps, not 24px/32px. Data density is a feature.
- NO gradient backgrounds. NO glassmorphism. NO backdrop-blur on main content.

## Component Specifics

### Dashboard
- 4 stat tiles: Leaderboard Rang, War Rang, Ø Trophäen, Aktiv 24h
  → Tiles: border only, no fill, number in Rajdhani bold
- War card (right): rank "#5" in 4rem gold, progress bars sharp, 
  Top 3 Fame as a minimal table row (not cards)
- Missing battles warning: left border accent (#c0392b), dark bg, mono font

### Rankings
- Full-width table, sticky header, alternating row bg (#0d0d0f / #141418)
- Rank column: mono font, gold for top 3
- Player name: primary text, slightly larger
- Stats columns: right-aligned, mono

### War Page
- Similar table structure for war participants
- Fame score in gold, battles done/remaining in secondary text

## What to avoid
- No pastel colors
- No border-radius > 4px
- No box-shadow for depth (use borders instead)
- No Inter/Roboto/system fonts  
- No centered hero layouts
- No "feature card" patterns with icons + descriptions
- No animated gradients or glow effects on main UI elements

Apply this consistently across all pages and components. 
Existing functionality must not be changed — only styles.