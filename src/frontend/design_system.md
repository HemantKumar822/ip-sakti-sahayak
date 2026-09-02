# IP-SAKTI Sahayak — Design System (Apple Cupertino & Notion Fusion)

This document outlines the design tokens, visual principles, and component specifications for the **IP-SAKTI Sahayak** frontend, engineered with Apple Cupertino minimalism and Notion's clean, document-first aesthetic.

---

## 🎨 Color Palette & Material Surfaces

| Token | Value | Material | Usage |
|---|---|---|---|
| `--color-canvas` | `#faf9f7` | Warm Canvas | Ambient background canvas with subtle radial light |
| `--color-surface` | `#ffffff` | Pure White | Elevated cards, memorandum paper, modal panels |
| `--color-border` | `#e8e7e3` | Subtle Hairline | Ultra-fine dividing lines, card outlines |
| `--color-border-subtle` | `rgba(0,0,0,0.06)` | Translucent Hairline | Specular inner card borders |
| `--color-text-primary` | `#191714` | High-Contrast Ink | Primary statutory headings, legal advisory prose |
| `--color-text-secondary` | `#6e6d69` | Annotation Slate | Secondary metadata, captions, reasoning HUD |
| `--color-accent` | `#0071e3` | Cupertino Blue | Active interactive elements, statutory citation pills |
| `--color-success` | `#1aae39` | Emerald Green | Verified answers, pulse-dot status indicator |
| `--color-warning` | `#dd5b00` | Amber Orange | Access and Benefit Sharing (ABS) compliance notices |
| `--color-error` | `#e03e3e` | Crimson Red | Safe abstentions, system notices |

### Frosted Glass & Specular Bevels
- **Glass Surface:** `rgba(255, 255, 255, 0.88)`
- **Glass Blur:** `backdrop-filter: blur(20px) saturate(180%)`
- **Specular Inset:** `box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9)`

---

## ✍️ Typography

The typography stack combines **Inter** (SF Pro Display characteristics with tight optical tracking) and **JetBrains Mono** for statutory section numbers and legal identifiers.

| Token | Size | Weight / Tracking | Usage |
|---|---|---|---|
| `--text-xs` | `12px` | Semibold (600, -0.005em) | Eyebrow tags, category badges, telemetry labels |
| `--text-sm` | `14px` | Regular (400) / Medium (500) | Metadata bar, reasoning HUD, source links |
| `--text-base` | `16px` | Regular (400, -0.011em) | Primary legal advisory prose |
| `--text-lg` | `20px` | Bold (700, -0.015em) | Section titles, memorandum headings |
| `--text-xl` | `32px` | Bold (700, -0.025em) | Hero workstation header |

---

## 📐 Spacing Scale (8px Grid)

| Token | Value | Common Application |
|---|---|---|
| `--space-1` | `4px` | Pill padding, micro-offsets |
| `--space-2` | `8px` | Badge gaps, button vertical padding, caption spacing |
| `--space-3` | `12px` | Bento gaps, callout internal padding |
| `--space-4` | `16px` | Standard element gap, card margin, container padding |
| `--space-6` | `24px` | Section vertical rhythm, memorandum padding |
| `--space-8` | `32px` | Major section breaks, top bar bottom margin |
| `--space-12` | `48px` | Footer top margin, hero separation |

---

## 🔘 Radius Scale & Tactile Physics

| Token | Value | Application |
|---|---|---|
| `--radius-sm` | `6px` | Inline code chips, HUD metric blocks |
| `--radius-md` | `12px` | Bento scenario cards, compliance callouts |
| `--radius-lg` | `16px` | Legal memorandum cards |
| `--radius-pill` | `9999px` | Statutory citation pills, category badges |

### Micro-Motion Physics
- **Spring Curve:** `cubic-bezier(0.2, 0.8, 0.2, 1)`
- **Hover Lift:** `transform: translateY(-2px)` with specular ambient glow
- **Active Tactile Press:** `transform: scale(0.98)` on click

---

## 🧩 Elevated Components

### 1. Selected Statutory Verification Bento Grid
Interactive 2x2 empty state grid showcasing landmark legal queries (Classical Ayurveda Section 3(p), Withanolide Synergy under Novartis Section 3(d), Foreign ABS under Section 6, and Trademark Genericness under Section 9).

### 2. The Reasoning Capsule (Dynamic Island Style)
A floating translucent pill (`⚡ Verified against N statutory authorities • XX% Confidence`) with a pulsating emerald status dot. Expands into a 4-metric HUD (Anti-Hallucination Score, Retrieval Engine, Latency, DPDP Privacy Hash).

### 3. Clickable Statutory Citation Badges
Pill badges with direct outbound links to official gazettes on IP India and Indian Kanoon.

### 4. Legal Memorandum Export Action Bar
1-Click `.md` memorandum generator that packages timestamp, jurisdiction, statutory citations, ABS clearance checklist, and non-patentability risk matrix into a formal legal brief.
