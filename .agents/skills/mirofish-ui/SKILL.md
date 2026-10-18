---
name: mirofish-ui
description: Design system, UI patterns, and component conventions for the MiroFish Vue 3 frontend application.
---

# MiroFish UI & Design System Guide

This skill governs all frontend interface development for MiroFish. MiroFish is a multi-agent social simulation and predictive intelligence engine with a signature neo-brutalist, cybernetic, high-density dashboard aesthetic.

## 1. Visual Language & Tokens

### Typography
- **Primary Display & Headings:** `'Space Grotesk', system-ui, sans-serif`
- **Monospace, Data & Code:** `'JetBrains Mono', monospace`
- **CJK Fallback:** `'Noto Sans SC', system-ui, sans-serif`

### Color Palette
- **Obsidian / Pure Black:** `#000000` (Headers, high-contrast borders, solid buttons)
- **Deep Slate:** `#111111` / `#1A1A1A`
- **Signal Orange (Accent):** `#FF5C00` / `#FF4500` (Active states, live indicators, primary highlights)
- **Clean White:** `#FFFFFF` (Card surfaces, clean backgrounds)
- **Structural Gray:** `#F5F5F5` / `#FAFAFA` (Panel backgrounds, subtle zebra striping)
- **Borders & Dividers:** `#E5E5E5` / `#E0E0E0` (Precise 1px borders)
- **Alert Colors:**
  - Critical / Misinformation: `#DC2626` / `#EF4444`
  - High / Urgent: `#EA580C` / `#F97316`
  - Warning / Burst: `#D97706` / `#F59E0B`
  - Success / Verified: `#16A34A` / `#22C55E`
  - Neutral / Unverified: `#6B7280`

### Geometry & Spatial Structure
- **Borders:** Crisp `1px solid` borders. Avoid fuzzy drop shadows; use sharp borders or hard-edge shadows `box-shadow: 2px 2px 0px #000000`.
- **Corner Radii:** Strict 0px to 4px max. Retain geometric, precision-engineered feel.
- **Micro-indicators:** Geometric markers (`■`, `◇`, `●`, `▲`, `▼`, `↗`).

## 2. Component Guidelines

### Navigation Bars
- Always include the bold monospaced brand header `MIROFISH`.
- Integrate `<LanguageSwitcher />` and route links with live status indicators.
- Provide clear route crumb or mode indicator.

### Data Tables & Queues
- Use monospaced numbers, timestamps, and IDs (`font-family: var(--font-mono)`).
- Status badges with distinct pill backgrounds and colored indicator dots.
- Interactive actions must provide immediate visual feedback (loading spinners, disabled state).
- Always include empty states that guide the user rather than leaving blank spaces.

### Internationalization (i18n)
- All user-visible strings must be translated in `locales/en.json` and `locales/zh.json`.
- Access translations using `$t('path.to.key')` or `useI18n()`.
