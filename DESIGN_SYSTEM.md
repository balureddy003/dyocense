# Modern SaaS Design System

## Overview

This design system provides a comprehensive, professional visual language for the Dyocense SMB platform. It emphasizes clarity, consistency, and modern SaaS aesthetics.

## Color Palette

### Brand Colors (Premium Indigo)

```css
--brand-50:  #F0F1FF  /* Lightest tint - backgrounds */
--brand-100: #E0E2FF  /* Very light - hover states */
--brand-200: #C7CBFF  /* Light - borders, disabled states */
--brand-300: #A5ABFF  /* Medium light - secondary elements */
--brand-400: #8188FF  /* Medium - inactive states */
--brand-500: #6366F1  /* PRIMARY - main brand color */
--brand-600: #5558E3  /* Medium dark - hover states */
--brand-700: #4A4DD1  /* Dark - active states */
--brand-800: #3E41B8  /* Very dark - headings */
--brand-900: #31349A  /* Darkest - emphasis */
```

### Semantic Colors

#### Success (Green)

- **Primary**: `#10B981` (green-500)
- **Background**: `#ECFDF5` (green-50)
- **Dark**: `#047857` (green-700)
- **Use**: Success messages, confirmations, positive metrics

#### Warning (Amber)

- **Primary**: `#F59E0B` (yellow-500)
- **Background**: `#FFFBEB` (yellow-50)
- **Dark**: `#B45309` (yellow-700)
- **Use**: Warnings, caution states, pending actions

#### Error (Red)

- **Primary**: `#EF4444` (red-500)
- **Background**: `#FEF2F2` (red-50)
- **Dark**: `#B91C1C` (red-700)
- **Use**: Errors, destructive actions, alerts

#### Info (Blue)

- **Primary**: `#3B82F6` (blue-500)
- **Background**: `#EFF6FF` (blue-50)
- **Dark**: `#1D4ED8` (blue-700)
- **Use**: Information, tips, neutral messages

### Accent Colors

- **Violet**: `#8B5CF6` - For gradient accents
- **Teal**: `#14B8A6` - For secondary highlights

### Surface Colors

```css
--surface-primary:   #FFFFFF  /* Main backgrounds */
--surface-secondary: #F8F9FA  /* Secondary backgrounds */
--surface-tertiary:  #F1F3F5  /* Tertiary backgrounds */
--surface-muted:     #E9ECEF  /* Muted backgrounds */
--surface-overlay:   rgba(255, 255, 255, 0.95)  /* Overlay backgrounds */
```

### Text Colors

```css
--text-primary:   #212529  /* Headings, important text */
--text-secondary: #495057  /* Body text, descriptions */
--text-tertiary:  #868E96  /* Secondary info, labels */
--text-muted:     #ADB5BD  /* Placeholders, hints */
--text-disabled:  #CED4DA  /* Disabled text */
```

## Typography

### Font Family

- **Primary**: `Inter var` with font feature settings
- **Monospace**: `JetBrains Mono` for code

### Font Feature Settings

```css
font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';
```

Enables:

- `cv02`: Open digits
- `cv03`: Disambiguation (l vs 1)
- `cv04`: Open four
- `cv11`: Simplified g

### Heading Scale

| Level | Size | Line Height | Weight | Usage |
|-------|------|-------------|--------|-------|
| h1 | 2.75rem (44px) | 1.2 | 800 | Page titles, hero headings |
| h2 | 2rem (32px) | 1.3 | 700 | Section headings |
| h3 | 1.5rem (24px) | 1.4 | 600 | Subsection headings |
| h4 | 1.25rem (20px) | 1.4 | 600 | Card titles |
| h5 | 1.125rem (18px) | 1.5 | 600 | Small headings |
| h6 | 1rem (16px) | 1.5 | 600 | Labels, captions |

### Body Text

- **Large**: `1.125rem` (18px) - Introductory text, important paragraphs
- **Base**: `1rem` (16px) - Default body text
- **Small**: `0.875rem` (14px) - Secondary information
- **Extra Small**: `0.75rem` (12px) - Captions, metadata

## Spacing Scale

```css
--space-xs:  0.625rem  /* 10px - tight spacing */
--space-sm:  0.75rem   /* 12px - compact spacing */
--space-md:  1rem      /* 16px - default spacing */
--space-lg:  1.25rem   /* 20px - comfortable spacing */
--space-xl:  1.5rem    /* 24px - spacious */
--space-2xl: 2rem      /* 32px - section spacing */
--space-3xl: 3rem      /* 48px - large section spacing */
```

## Border Radius

```css
--radius-xs:   0.375rem  /* 6px - small elements */
--radius-sm:   0.5rem    /* 8px - buttons, badges */
--radius-md:   0.75rem   /* 12px - cards, inputs */
--radius-lg:   1rem      /* 16px - panels, modals */
--radius-xl:   1.5rem    /* 24px - large panels */
--radius-full: 9999px    /* Full circle - pills, avatars */
```

## Shadow System

### Standard Shadows

```css
--shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
  /* Subtle elevation - hover states */
  
--shadow-sm: 0 2px 8px 0 rgba(0, 0, 0, 0.08), 0 1px 3px 0 rgba(0, 0, 0, 0.04)
  /* Small cards, dropdowns */
  
--shadow-md: 0 4px 16px 0 rgba(0, 0, 0, 0.12), 0 2px 4px 0 rgba(0, 0, 0, 0.06)
  /* Cards, panels - default elevation */
  
--shadow-lg: 0 12px 32px 0 rgba(0, 0, 0, 0.15), 0 4px 8px 0 rgba(0, 0, 0, 0.08)
  /* Modals, popovers - high elevation */
  
--shadow-xl: 0 24px 48px 0 rgba(0, 0, 0, 0.18), 0 8px 16px 0 rgba(0, 0, 0, 0.10)
  /* Overlays, drawers - maximum elevation */
```

### Brand Shadows (Colored Glow)

```css
--shadow-brand-sm: 0 4px 12px 0 rgba(99, 102, 241, 0.15)
  /* Subtle brand glow */
  
--shadow-brand-md: 0 8px 24px 0 rgba(99, 102, 241, 0.25)
  /* Medium brand glow - hover states */
  
--shadow-brand-lg: 0 16px 48px 0 rgba(99, 102, 241, 0.35)
  /* Strong brand glow - active states */
```

## Gradients

### Brand Gradients

```css
/* Primary Brand */
.bg-gradient-brand {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
}

/* Reverse Brand */
.bg-gradient-brand-reverse {
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
}

/* Vibrant Multi-color */
.bg-gradient-brand-vibrant {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #14B8A6 100%);
}
```

### Subtle Background Gradients

```css
/* Vertical Fade */
.bg-gradient-subtle {
  background: linear-gradient(180deg, #FFFFFF 0%, #F8F9FA 100%);
}

/* Surface with Brand Tint */
.bg-gradient-surface {
  background: linear-gradient(135deg, #FFFFFF 0%, #F0F1FF 100%);
}
```

### Text Gradients

```css
.text-gradient-brand {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

## Glassmorphism

### Standard Glass Panel

```css
.glass-panel {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}
```

### Brand Glass Panel

```css
.glass-panel-brand {
  background: linear-gradient(
    135deg,
    rgba(99, 102, 241, 0.1) 0%,
    rgba(139, 92, 246, 0.05) 100%
  );
  backdrop-filter: blur(12px);
  border: 1px solid rgba(99, 102, 241, 0.2);
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15);
}
```

## Transitions

```css
--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1)
  /* Quick interactions - hover, focus */
  
--transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1)
  /* Default transitions - most UI changes */
  
--transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1)
  /* Slower transitions - page transitions, reveals */
```

## Component Patterns

### Buttons

#### Primary Button

```tsx
<Button
  className="btn-gradient"
  size="md"
  radius="md"
>
  Primary Action
</Button>
```

- Gradient background
- White text, weight 600
- Hover: lifts 1px, stronger shadow
- Active: returns to original position

#### Secondary Button

```tsx
<Button
  variant="outline"
  color="brand"
  size="md"
>
  Secondary Action
</Button>
```

### Cards

#### Elevated Card (Default)

```tsx
<div className="card-elevated">
  {/* content */}
</div>
```

- White background
- Subtle border and shadow
- Hover: stronger shadow + brand border color

#### Premium Card

```tsx
<div className="card-premium">
  {/* content */}
</div>
```

- Gradient background (white → brand tint)
- Brand-colored border
- Brand shadow glow

### Badges

#### Gradient Badge

```tsx
<span className="badge-gradient">
  New Feature
</span>
```

#### Outline Badge

```tsx
<span className="badge-outline-brand">
  Beta
</span>
```

### Interactive Effects

#### Hover Lift

```css
.hover-lift {
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}
.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}
```

#### Hover Glow

```css
.hover-glow:hover {
  box-shadow: var(--shadow-brand-md);
  border-color: var(--brand-primary);
}
```

## Animation Utilities

### Pulse Effect

```css
.pulse-brand {
  animation: pulse-brand 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
```

Use for: Loading states, notifications, attention-grabbers

### Gradient Shift

```css
.bg-gradient-animated {
  background: linear-gradient(270deg, #6366F1, #8B5CF6, #14B8A6);
  background-size: 400% 400%;
  animation: gradient-shift 15s ease infinite;
}
```

Use for: Hero sections, premium features

### Shimmer (Loading Skeleton)

```css
.skeleton {
  background: linear-gradient(90deg, #F1F3F5 0%, #E9ECEF 50%, #F1F3F5 100%);
  background-size: 468px 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
```

## Accessibility

### Color Contrast

All color combinations meet **WCAG AA** standards:

- Normal text: minimum 4.5:1 contrast ratio
- Large text (18px+): minimum 3:1 contrast ratio
- UI components: minimum 3:1 contrast ratio

### Focus States

```css
.focus-brand:focus {
  outline: none;
  border-color: var(--brand-primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}
```

All interactive elements have visible focus indicators.

### Reduced Motion

Animations respect `prefers-reduced-motion` preference:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Usage Guidelines

### DO ✅

- Use brand colors for primary actions and key UI elements
- Apply gradients sparingly for emphasis (CTAs, hero sections)
- Maintain consistent spacing using the spacing scale
- Use semantic colors for their intended purpose (success = green)
- Apply shadows to create visual hierarchy
- Use glassmorphism for overlays and floating panels

### DON'T ❌

- Mix multiple gradients on the same screen section
- Use brand colors for destructive actions (use red)
- Apply animations to every element (performance + distraction)
- Override semantic colors for decorative purposes
- Use extreme color combinations without checking contrast
- Nest glass panels (reduces clarity)

## Component Library Integration

### Mantine Theme

The design system is configured in `main.tsx`:

```typescript
const theme = createTheme({
  primaryColor: 'brand',
  colors: { brand, dark, green, yellow, red, violet, teal },
  fontFamily: 'Inter var, ...',
  shadows: { ... },
  // ... complete configuration
})
```

### CSS Custom Properties

All design tokens available as CSS variables in `styles.css`:

```css
:root {
  --brand-primary: #6366F1;
  --shadow-md: 0 4px 16px 0 rgba(0, 0, 0, 0.12);
  /* ... all tokens */
}
```

### Utility Classes

Comprehensive utility classes for:

- Gradients (`.bg-gradient-brand`, `.text-gradient-brand`)
- Effects (`.glass-panel`, `.hover-lift`, `.hover-glow`)
- Cards (`.card-elevated`, `.card-premium`)
- Badges (`.badge-gradient`, `.badge-outline-brand`)
- Animations (`.pulse-brand`, `.skeleton`)

## Maintenance

### Adding New Colors

1. Define color scale (50-900) in `main.tsx` theme
2. Add CSS custom properties in `styles.css`
3. Create utility classes if needed
4. Update this documentation

### Updating Shadows

1. Modify shadow values in both locations:
   - `main.tsx` theme.shadows
   - `styles.css` CSS variables
2. Test across components for consistency
3. Update documentation with new values

### Creating New Components

1. Follow established patterns (buttons, cards)
2. Use design tokens (colors, spacing, shadows)
3. Ensure accessibility (focus states, contrast)
4. Add to component library with examples

## Resources

- **Design Tokens**: `/apps/smb/src/main.tsx` + `/apps/smb/src/styles.css`
- **Utility Classes**: `/apps/smb/src/styles.css` (bottom section)
- **Mantine Docs**: <https://mantine.dev/>
- **WCAG Guidelines**: <https://www.w3.org/WAI/WCAG21/quickref/>

---

**Version**: 1.0  
**Last Updated**: 2024  
**Status**: Active
