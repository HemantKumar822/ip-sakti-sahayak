# IP-SAKTI Sahayak — Design System (Notion-Inspired)

This document outlines the design tokens, visual principles, and component specifications for the **IP-SAKTI Sahayak** frontend, modeled after Notion's clean, minimalist, and document-first aesthetic.

---

## 🎨 Color Palette

| Token | Value | Swatch | Usage |
|---|---|---|---|
| `--color-canvas` | `#FFFFFF` | ⚪ White | Page background canvas, crisp cards |
| `--color-surface` | `#F7F6F3` | 🔘 Light Gray | Notion-style soft background, top bar, input containers |
| `--color-border` | `#E9E9E7` | 🔲 Border Gray | Subtle dividing lines, card hairlines, input bottom border |
| `--color-text-primary` | `#37352F` | ⚫ Dark Charcoal | Primary headings, body copy, active CTA background |
| `--color-text-secondary` | `#9B9A97` | 🔘 Muted Gray | Metadata, placeholders, captions, jurisdiction notes |
| `--color-accent` | `#2EAADC` | 🔵 Notion Blue | Active states, focus rings, link highlights |
| `--color-success` | `#0F7B6C` | 🟢 Forest Green | Answered state, positive verification signals |
| `--color-warning` | `#E9A849` | 🟠 Warm Amber | Access and Benefit Sharing (ABS) alerts |
| `--color-error` | `#E03E3E` | 🔴 Soft Red | Honest abstention notices, critical system errors |

---

## ✍️ Typography

The typography stack uses **Inter** for crisp document readability and **JetBrains Mono** for code / statutory identifiers.

| Token | Size | Weight / Tracking | Usage |
|---|---|---|---|
| `--text-xs` | `0.75rem` (12px) | Regular (400) | Captions, jurisdiction notes, metadata, footer |
| `--text-sm` | `0.875rem` (14px) | Medium (500) / Regular | Button labels, callout descriptions, system badges |
| `--text-base` | `1.00rem` (16px) | Regular (400) | Body guidance, advisory prose |
| `--text-lg` | `1.125rem` (18px) | Regular (400) | Main query input field, subheadings |
| `--text-xl` | `1.50rem` (24px) | Bold (700, -0.02em) | Main page title / question prompt |

---

## 📐 Spacing Scale (8px Grid)

| Token | Value | Common Application |
|---|---|---|
| `--space-1` | `4px` | Badge internal padding, hairline offsets |
| `--space-2` | `8px` | Tight gaps, button vertical padding, caption spacing |
| `--space-3` | `12px` | Pill padding, callout internal padding |
| `--space-4` | `16px` | Standard element gap, card margin, container padding |
| `--space-6` | `24px` | Section vertical rhythm, card internal padding |
| `--space-8` | `32px` | Major section breaks, top bar bottom margin |
| `--space-12` | `48px` | Footer top margin, hero separation |

---

## 🔘 Radius Scale

| Token | Value | Application |
|---|---|---|
| `--radius-sm` | `4px` | Buttons, badges, callout boxes, form inputs |
| `--radius-md` | `8px` | Response cards, modal containers |
| `--radius-lg` | `12px` | Floating elevated panels |

---

## 🧩 Key Components

### 1. Top Bar
- **Height:** `48px`
- **Background:** `var(--color-surface)` (`#F7F6F3`)
- **Border:** 1px bottom border `var(--color-border)`
- **Content:** System brand on left (`IP-SAKTI Sahayak`), Jurisdiction pill on right (`[India 🇮🇳]`).

### 2. Query Input
- **Style:** Minimalist, borderless canvas with a subtle bottom hairline (`1px solid var(--color-border)`).
- **Typography:** `var(--text-lg)` with `var(--color-text-secondary)` placeholder text.
- **Focus:** Sharp border-bottom transition to `var(--color-text-primary)` without heavy outer focus rings.

### 3. Action Button
- **Background:** `var(--color-text-primary)` (`#37352F`)
- **Text:** `#FFFFFF`, `var(--text-sm)`, medium weight
- **Hover:** Opacity `0.9`
- **Disabled:** Opacity `0.4` with `not-allowed` cursor during in-flight queries.

### 4. Alert & Abstention Callouts
- **ABS Compliance Callout (`.callout-abs`):** Warm amber border (`--color-warning`) with `#FFFDF5` tinted background, dedicated to Biological Diversity Act & NBA Access and Benefit Sharing clearances.
- **TKDL Prior Art Callout (`.callout-tkdl`):** Deep indigo border (`#213183`) with `#F4F6FB` tinted background, dedicated to Section 3(p) Patents Act Traditional Knowledge exclusions.
- **Abstention Notice (`.callout-abstain`):** Soft red border (`--color-error`) with `#FDF3F3` tinted background and domain explanation.

### 5. Statutory Citation Badges (`.statutory-citation-badge`)
- **Visual Style:** Pill token (`border-radius: 9999px`), crisp `1px solid #D0D7DE`, `#F6F8FA` background, dark ink text (`#0969DA` link tone).
- **Interaction:** Hover micro-animation (subtle shadow, background tint transition, cursor pointer). Directly hyperlinked with `target="_blank"` to official government gazette PDFs.

### 6. Live Pipeline State Stepper (`.pipeline-stepper`)
- **Structure:** Horizontal flex chain of steps:
  `[🔒 PII Scrubbed] ➔ [🏷️ Categorized] ➔ [⚖️ Routed] ➔ [⚡ Hybrid Search] ➔ [🛡️ Gate Verified]`
- **Tokens:** Minimalist border, pill badges, active state indicators.

### 7. Quick-Launch Scenario Chips (`.quick-action-chip`)
- **Visual Style:** Soft gray pill buttons with icon prefix. Hover elevation and background transition.
- **Action:** Populates the query state and triggers immediate execution on click.

### 8. Technical Inspector Drawer (`.tech-inspector-drawer`)
- **Structure:** Collapsible metadata cockpit containing confidence score metric gauge, hybrid retrieval mode indicator (Dense + BM25 RRF), latency in milliseconds, and SHA-256 session hash.
