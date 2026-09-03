# IP-SAKTI Sahayak: Frontend Design System & Component Specification (React + Vite)

## 🏛️ Philosophy & Guiding Principles

The IP-SAKTI Sahayak frontend is engineered as a **Citation-Grounded AI Legal Workbench for Ayurveda & ABS Laws**.
Unlike consumer chat apps, this interface is designed for **patent attorneys, traditional medicine researchers, inventors, and compliance officers**. It prioritizes:
1. **Verifiability & Transparency:** Immediate statutory context, citation badging with government source links, and clear differentiation between Biological Diversity Act (ABS) compliance and Patents Act Section 3(p) (TKDL) exclusions.
2. **Minimal Cognitive Load:** Clean, Notion-inspired typography, subtle glassmorphism (`backdrop-filter: blur`), and intentional visual hierarchy.
3. **Deterministic Feedback:** Live pipeline state tracking, transparent confidence indicators, and honest abstention messaging.
4. **Privacy by Design:** Strict adherence to Digital Personal Data Protection (DPDP) Act principles — zero collection of personally identifiable information (PII).

---

## 🎨 Design Tokens (`src/web/src/styles/design_tokens.css`)

### Color Palette

| Token | Hex / Value | Visual Identity | Functional Role |
| :--- | :--- | :--- | :--- |
| `--color-bg-primary` | `#F7F6F3` | ⚪ Warm Notion Canvas | Application shell, topbar, footer |
| `--color-bg-secondary` | `#FFFFFF` | ⚪ Crisp Pure White | Chat canvas, user message bubbles, cards |
| `--color-text-primary` | `#37352F` | ⚫ Dark Charcoal | Headings, body copy, active CTA button |
| `--color-text-secondary` | `#9B9A97` | 🔘 Muted Slate | Metadata, captions, placeholders, timestamps |
| `--color-border` | `rgba(55, 53, 47, 0.16)` | 🔲 Subtle Border | Cards, inputs, message wrappers |
| `--color-border-light` | `rgba(55, 53, 47, 0.08)` | ▫️ Hairline Border | Separators, headers, footers |
| `--color-accent` | `#2EAADC` | 🔵 Notion Blue | Active states, focus outlines, link highlights |
| `--color-success` | `#1aae39` | 🟢 Emerald Green | Completed pipeline stages, verified statuses |
| `--color-warning` | `#dd5b00` | 🟠 Amber Orange | Biological Diversity Act / ABS warnings |
| `--color-warning-bg` | `#FFF3CD` | 🟡 Warm Amber Tint | Background for ABS compliance callouts |
| `--color-error` | `#e03e3e` | 🔴 Crimson Red | Abstention notices, service errors |
| `--color-error-bg` | `#FEE2E2` | 🔴 Light Red Tint | Background for error callouts |
| `--color-info` | `#1e40af` | 🔵 Deep Royal Blue | Section 3(p) Traditional Knowledge notices |
| `--color-info-bg` | `#eff6ff` | 🔵 Soft Blue Tint | Background for TKDL prior art callouts |

---

## 🧩 React Component Architecture (`src/web/src/components/`)

### 1. `ChatInterface.tsx`
- **Role:** Central conversational canvas managing message history, streaming feedback, error states, and query submission.
- **Privacy Assurance:** Only submits anonymized `query_text`, client-generated cryptographic `session_id`, and prior conversation turns. No PII fields exist.
- **Animation:** Utilizes `animate-fade-in` (`slideUpFadeIn` CSS keyframe) for graceful card entries.

### 2. `StatutoryBadge.tsx`
- **Role:** Interactive pill badge representing primary statutory authorities (e.g. *Patents Act 1970 (S. 3(p))*, *Biological Diversity Act 2002 (S. 6)*).
- **Behavior:** Renders clickable pill with official gazette link icon that opens canonical government source PDFs in a secure `target="_blank" rel="noopener noreferrer"` window.

### 3. `Callout.tsx`
- **Role:** High-visibility contextual alert box tailored to legal requirements:
  - `abs`: Alerts user when biological resources trigger mandatory NBA / SBB approval under Sections 3, 4, or 6 of the Biological Diversity Act.
  - `tkdl`: Alerts user when traditional knowledge triggers non-patentability exclusions under Section 3(p) of the Patents Act.
  - `abstain`: Displays graceful refusals when query falls outside the statutory Ayurvedic corpus.
  - `error`: Displays clean, actionable resilience recovery instructions.

### 4. `PipelineStepper.tsx`
- **Role:** Real-time visual lifecycle tracker illustrating multi-stage verification:
  `[🔒 PII Scrubbed] ➔ [🏷️ Categorized] ➔ [⚖️ Routed] ➔ [⚡ Hybrid Search] ➔ [🛡️ Gate Verified]`

### 5. `HeroState.tsx`
- **Role:** Onboarding experience displayed when the workbench initializes with zero query history.
- **Components:** Top event pill badge, authoritative value proposition title and subtitle, 4 trust capability indicators, and 4 interactive, clickable legal scenario brief cards (Classical Ayurveda § 3(p), Biological Resource ABS § 6, Enhanced Efficacy § 3(d), and Trademark distinctiveness).
- **Interaction:** Clicking any scenario immediately populates the inquiry and triggers analysis.

### 6. `Topbar.tsx`
- **Role:** Sticky application header with branded seal logo, live legal core status indicator with green pulse, "New Inquiry" session reset button, and jurisdiction indicator.

### 7. `CitationsDrawer.tsx`
- **Role:** Collapsible evidentiary drawer that reveals detailed quoted snippets, document classifications, retrieval timestamps, and direct links to official government gazette records.

---

## ⚖️ Legal Disclaimer
Every page renders the statutory disclaimer:
> *"This information is provided for general awareness and does not constitute legal advice. Consult a qualified IP attorney for decisions specific to your situation."*
