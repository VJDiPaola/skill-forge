---
name: "glassmorphic-ui"
description: "Generate a dark glassmorphic CSS design system with variables, utilities, and component styles. Use when the user asks for a glassmorphic look, frosted-glass panels, or a dark translucent design system."
---
Generate a complete dark glassmorphic CSS design system with variables, utility classes, and component styles. This creates a modern, translucent UI with depth and subtle glow effects.

## What to generate

Ask the user:
1. What CSS approach? (plain CSS, CSS modules, Tailwind, styled-components)
2. What accent colors? Default to blue (#4fc3f7) / orange (#e07c4f) / purple (#ab47bc) if unspecified
3. What font? Default to Inter if unspecified

Then generate the full system:

### 1. CSS Variable System

```css
:root {
  /* Glass properties */
  --glass-bg: rgba(12, 14, 28, 0.55);
  --glass-border: rgba(255, 255, 255, 0.08);
  --glass-hover: rgba(255, 255, 255, 0.04);
  --glass-blur: 20px;
  --glass-radius: 16px;

  /* Accent colors — customizable */
  --accent-blue: #4fc3f7;
  --accent-orange: #e07c4f;
  --accent-purple: #ab47bc;

  /* Text hierarchy */
  --text-primary: #f0f2f8;
  --text-secondary: #9ca3b4;
  --text-muted: #636b7e;
}
```

### 2. Base Glass Class

```css
.glass {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
}
```

### 3. Opacity Tier System

Use consistent opacity levels for visual hierarchy:
- `rgba(255, 255, 255, 0.02)` — barely visible, sunken panels
- `rgba(255, 255, 255, 0.04)` — hover states, subtle emphasis
- `rgba(255, 255, 255, 0.06)` — active states, elevated surfaces
- `rgba(255, 255, 255, 0.08)` — borders, dividers
- `rgba(255, 255, 255, 0.10)` — prominent borders, hover borders
- `rgba(8, 10, 22, 0.55-0.85)` — glass panel backgrounds (higher = more opaque)

### 4. Multi-Layer Background

```css
.app {
  background:
    radial-gradient(ellipse at 20% 50%, rgba(79, 195, 247, 0.06) 0%, transparent 60%),
    radial-gradient(ellipse at 80% 20%, rgba(171, 71, 188, 0.05) 0%, transparent 50%),
    radial-gradient(ellipse at 60% 80%, rgba(224, 124, 79, 0.04) 0%, transparent 50%),
    linear-gradient(180deg, #060612 0%, #0a0c1a 50%, #060612 100%);
}
```

### 5. Interactive States

```css
/* Hover transitions — consistent 0.2s ease */
.interactive-element {
  transition: all 0.2s ease;
}
.interactive-element:hover {
  background: var(--glass-hover);
  color: var(--text-primary);
}

/* Input focus glow */
input:focus {
  border-color: rgba(79, 195, 247, 0.4);
  background: rgba(255, 255, 255, 0.06);
  box-shadow: 0 0 20px rgba(79, 195, 247, 0.08);
}

/* Gradient text accent */
.gradient-text {
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

### 6. Custom Scrollbar

```css
.scrollable::-webkit-scrollbar {
  width: 4px;
}
.scrollable::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}
```

### 7. Component Patterns

Include styles for these common glass components:
- **Header bar** — `rgba(8, 10, 22, 0.7)` with `blur(24px)`, bottom border
- **Sidebar** — `rgba(8, 10, 22, 0.6)` with `blur(24px)`, right border
- **Detail panel** — `rgba(8, 10, 22, 0.65)` with `blur(24px)`, left border
- **Dropdown/popover** — `rgba(12, 14, 28, 0.85)` with `blur(24px)`, shadow `0 16px 48px rgba(0, 0, 0, 0.5)`
- **Sunken panel** — `rgba(255, 255, 255, 0.02)` with border `rgba(255, 255, 255, 0.04)`
- **Badge/tag** — inline-block, small border-radius, uppercase, 10px font, accent bg
- **Close button** — `rgba(255, 255, 255, 0.06)` bg, border, 30x30px, rounded

### 8. Section Headers

```css
h3.section-title {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-muted);
  font-weight: 600;
}
```

## Important design principles
- Blur should be consistent within layout tier: 24px for main panels, 20px for general glass, 12-14px for small elements
- Never use pure white (#fff) for large text areas — use --text-primary (#f0f2f8)
- Borders are always subtle (0.06-0.10 opacity white), never sharp
- Hover states add +0.02-0.04 opacity, never dramatic jumps
- Shadows only on floating elements (dropdowns, popovers), panels use borders
- The background gradient colors should use your accent colors at very low opacity (0.04-0.06)

$ARGUMENTS
