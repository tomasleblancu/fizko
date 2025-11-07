# Fizko Application Styling Analysis: App vs Landing Page

## Executive Summary

The Fizko application uses **two distinct styling approaches**:

1. **Landing Page**: Modern, marketing-focused design with vibrant gradients, animations, and premium visual effects
2. **Main Application**: Minimal, functional design focused on data visualization and productivity

This creates a significant visual inconsistency where the landing page appears far more polished and premium than the app users interact with daily.

---

## Part 1: Global Styling Foundation

### Tailwind CSS Configuration
**File**: `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/tailwind.config.ts`

**Design Tokens**:
- **Font Family**: Questrial (primary), system fonts as fallback
- **Color System**: Limited to Tailwind defaults + 2 surface colors
- **Custom Colors**:
  - `surface.light`: `#f3f4f6` (Gray-100)
  - `surface.dark`: `#0b1120` (Very dark navy)
- **Dark Mode**: Enabled via CSS class (`darkMode: "class"`)

**Animations Defined**:
- `blob` - 7-second random movement
- `heartbeat-left`, `heartbeat-right` - Interactive element animations
- `pulse-once` - Single pulse effect

### Global CSS
**File**: `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/app/styles/index.css`

**Features**:
- Tailwind directives (base, components, utilities)
- Multiple animation definitions (blob, spin, fade, bounce, etc.)
- Custom animation delays (100ms - 500ms intervals)
- ChatKit logo replacement (SVG rendering with brightness filters)
- Dark mode inversion for ChatKit logo

---

## Part 2: Landing Page Styling

**File**: `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/pages/home/ui/Landing.tsx`

### Hero Section
```
Background: 
  - Main gradient: blue-50 → white → purple-50 (light mode)
  - Dark gradient: gray-900 → gray-800 → gray-900
  - Decorative wave gradient: blue-100/50 fading to transparent

Typography:
  - Logo container: Clickable with special sizing (h-16 sm:h-20 md:h-24)
  - Main headline: text-xl sm:text-4xl, font-bold, animated typing effect
  - Gradient text: blue-600 → purple-600 with bg-clip-text
  - Subtitle: text-xl, text-gray-600, max-width constraint

Buttons:
  - Primary CTA: gradient-to-r from-blue-600 to-purple-600
  - Styling: rounded-full, px-8, py-4, text-lg, font-semibold
  - Effects: shadow-xl, hover:shadow-2xl, hover:scale-105
  - Secondary button: Border-based with white background
```

### "Las 3C de Fizko" Section
```
Background:
  - Dark gradient: slate-900 → blue-900 → slate-900
  - Decorative blurred circles: blue-500 and purple-500 (top/bottom)
  - Semi-transparent overlay (opacity-20)

Cards (3 columns):
  - Background: white/10 with backdrop-blur-sm
  - Border: white/20, rounded-3xl
  - Icon containers: 14x14 units with gradient backgrounds
  - Hover effect: opacity increase on gradient background (25% → 40%)
  - Colors per card:
    1. "Conecta": Blue-cyan gradient
    2. "Controla": Purple-pink gradient
    3. "Cumple": Green-emerald gradient

Typography:
  - Headers: text-3xl, font-bold, text-white
  - Body: text-lg, text-blue-100, leading-relaxed
```

### Features Section
```
Background:
  - Dark gradient: slate-900 → slate-800 → slate-900
  - Connection line: emerald-500/50 → transparent

Cards (3 columns):
  - Background: gradient-to-br from-slate-800 to-slate-900
  - Borders: 2px, color-coded (blue/purple/green at 30% opacity)
  - Border hover: increase to 60% opacity
  - Icon containers: 16x16 units with colored gradients
  - Hover effect: icon scales up (scale-110)

Connection indicators:
  - Vertical lines with matching colors
  - Ring effects on circles (color-400/20)
```

### CTA Section
```
Background: linear-gradient from-blue-600 to-purple-600
Button: white background with gradient text color, larger sizing
```

### Key Landing Page Features
- **Rich animations**: TypeAnimation, blob animations, gradient text
- **Depth effects**: Multiple blur backgrounds, layered gradients
- **Premium feel**: Rounded corners (rounded-3xl), complex gradients, shadows
- **Video embeds**: Responsive video with auto-play
- **Dark mode support**: All elements have dark: variants
- **Interactive elements**: Hover scaling, opacity transitions, glow effects

---

## Part 3: Main Application Styling

### Home Component (Dashboard)
**File**: `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/features/dashboard/ui/Home.tsx`

```
Container Background:
  - Light: from-slate-100 via-white to-slate-200
  - Dark: from-slate-900 via-slate-950 to-slate-850
  - CSS gradient-to-br (no animations)

Layout:
  - Fixed, full-screen container (fixed inset-0)
  - Two-column layout on desktop: chat (35%) + content (65%)
  - Single column (reversed) on mobile: content above chat
  - No visual decoration or effects

Navigation Pills (Mobile):
  - Background: slate-100 / dark:slate-800
  - Button styling: rounded-lg, px-3 py-2
  - Active state: white background + emerald-600 text + shadow-sm
  - Hover: scale-105, background changes
  - Icon scaling: scale-110 when active
```

### Component Styling Characteristics
- **Minimal decorative effects**: Only essential UI elements
- **Functional color scheme**: Slate grays with emerald accents for active states
- **Clean borders**: slate-200/slate-800 at reduced opacity
- **Consistent spacing**: py-2, px-3/4, gap-1/2
- **No gradients**: Solid colors predominate
- **Simple shadows**: shadow-sm or no shadow

### Dashboard Cards
**File**: `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/features/dashboard/ui/TaxSummaryCard.tsx`

```
Card Container:
  - Light: bg-white/90, border-slate-200/70, border border-rounded-2xl
  - Dark: bg-slate-900/70, border-slate-800/70
  - No gradient backgrounds

Content Sections:
  - Metric cards: Grid layout (2 columns on mobile)
  - Income card: border-emerald-200/60, bg-gradient-to-br from-emerald-50 to-white
  - Expense card: border-rose-200/60, bg-gradient-to-br from-rose-50 to-white
  - Note: Only light data sections use subtle gradients

Typography:
  - Metric headers: text-sm font-medium text-slate-600
  - Values: text-2xl or text-4xl font-bold
  - Color coding: emerald-600 for income, rose-600 for expenses

Interactions:
  - Hover: translateY(-1px) + box-shadow: 0 4px 12px rgba(0,0,0,0.08)
  - No scale transforms
  - Subtle animations only

Charts:
  - Recharts integration for data visualization
  - Dark mode: stroke colors change (slate-200 → slate-700)
  - Grid: subtle dashed lines
```

### Company Info Card
**File**: `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/features/dashboard/ui/CompanyInfoCard.tsx`

```
Card Background:
  - Light: border-slate-200/70, bg-gradient-to-br from-blue-50 to-purple-50
  - Dark: border-slate-800/70, dark:from-blue-950/30 dark:to-purple-950/30
  - Padding: p-3 (compact)

Logo Integration:
  - Fizko logo (8x8 units)
  - Positioned left side
  - Text truncation for long names

Hover State (Chateable):
  - translateY(-1px)
  - box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08)
```

### Chateable Component Styling
**File**: `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/app/styles/chateable.css`

```
Wrapper (.chateable-wrapper):
  - display: contents (transparent to DOM)
  - Cursor: pointer
  - Child element transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1)

Hover Effect:
  - translateY(-1px)
  - box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08)

Element (.chateable-element):
  - Pseudo-element overlay (::before) with rgba(59, 130, 246, 0.06)
  - Blue focus ring: rgba(59, 130, 246, 0.5)
  - Active state: small shadow reduction

Focus:
  - outline: 2px solid rgba(59, 130, 246, 0.5)
  - outline-offset: 2px
```

### Component Library
**Files**: `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/shared/components/ui/`

#### Button Component
```
Variants:
  - default: bg-blue-600 text-white hover:bg-blue-700
  - destructive: bg-red-600 text-white hover:bg-red-700
  - outline: border border-gray-300 hover:bg-gray-100
  - secondary: bg-gray-200 text-gray-900 hover:bg-gray-300
  - ghost: minimal styling
  - link: text styling with underline

Sizes:
  - default: h-10 px-4 py-2
  - sm: h-9 rounded-md px-3
  - lg: h-11 rounded-md px-8
  - icon: h-10 w-10

Base Styles:
  - rounded-md
  - font-medium
  - transition-colors
  - focus-visible:ring-2
  - disabled:opacity-50
```

#### Card Component
```
Card: rounded-lg border-gray-200 bg-white shadow-sm
CardHeader: flex flex-col space-y-1.5 p-6
CardTitle: text-2xl font-semibold
CardDescription: text-sm text-gray-500
CardContent: p-6 pt-0
```

---

## Part 4: Key Styling Differences

### 1. COLOR SCHEMES

| Aspect | Landing Page | Main App |
|--------|--------------|----------|
| **Primary colors** | Blue-600 to purple-600 gradients | Slate grays + emerald accents |
| **Background** | Vibrant gradients (blue/purple) | Neutral grays (slate) |
| **Accent colors** | Multiple (green, red, cyan, pink) | Primarily emerald-600 |
| **Border colors** | White/transparent on dark | Slate-200/800 at reduced opacity |
| **Text colors** | High contrast (white on dark) | Moderate contrast (slate-600/900) |

### 2. TYPOGRAPHY

| Aspect | Landing Page | Main App |
|--------|--------------|----------|
| **Font** | Questrial (custom) | Questrial system fallback |
| **Sizes** | Large headers (text-4xl sm:text-5xl) | Moderate (text-lg, text-2xl max) |
| **Weights** | Mix of font-bold, font-semibold | Consistent font-bold for values |
| **Line height** | leading-relaxed for body | leading-relaxed rarely used |

### 3. SPACING & LAYOUT

| Aspect | Landing Page | Main App |
|--------|--------------|----------|
| **Padding** | Generous (p-6, p-8, p-12) | Compact (p-3, p-4) |
| **Gaps** | Large gaps (gap-8) | Small gaps (gap-1, gap-2) |
| **Section padding** | py-24, py-16 | py-2, py-3, py-4 |
| **Max widths** | max-w-7xl, max-w-6xl | Full width with flex layout |

### 4. BORDER & SHADOWS

| Aspect | Landing Page | Main App |
|--------|--------------|----------|
| **Border radius** | Large (rounded-3xl, rounded-2xl) | Medium (rounded-lg, rounded-xl) |
| **Border style** | Transparent white borders | Translucent slate borders |
| **Shadows** | Heavy (shadow-xl, shadow-2xl) | Light (shadow-sm) |
| **Blur effects** | Extensive backdrop-blur-sm | None |

### 5. ANIMATION & INTERACTIVITY

| Aspect | Landing Page | Main App |
|--------|--------------|----------|
| **Animations** | TypeAnimation, blob, custom | Minimal (hover effects only) |
| **Hover effects** | scale-105, scale-110 transforms | translateY(-1px) only |
| **Transitions** | Multiple (duration-300, duration-500) | Single (duration-200) |
| **Decorative elements** | Animated blobs, gradients | None |
| **Duration** | 0.3s-0.5s | 0.2s |

### 6. GRADIENT USAGE

| Aspect | Landing Page | Main App |
|--------|--------------|----------|
| **Frequency** | Extensive (most sections) | Minimal (only data cards) |
| **Complexity** | Multi-color (3-4 stops) | Simple (2 stops) |
| **Opacity** | Full opacity for decorative elements | Low opacity for data sections |
| **Purpose** | Visual appeal and branding | Subtle data differentiation |

### 7. DARK MODE SUPPORT

| Aspect | Landing Page | Main App |
|--------|--------------|----------|
| **Implementation** | dark: variants throughout | Comprehensive dark: variants |
| **Consistency** | Inverts colors appropriately | Context-aware dark mode |
| **Contrast** | Maintained in dark mode | Maintained consistently |

---

## Part 5: Component Consistency Issues

### Inconsistent Button Styling
```
Landing Page:
  <button className="rounded-full bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-4">
    Gradient, oversized, round

Main App Button Component:
  <Button variant="default">
    bg-blue-600 (solid), standard sizing, rounded-md
```

### Inconsistent Card Styling
```
Landing Page Cards:
  - rounded-3xl (extra large)
  - Gradient backgrounds
  - backdrop-blur-sm
  - white/10 backgrounds with transparency
  - Complex hover states

Main App Cards:
  - rounded-lg (standard)
  - Solid or subtle gradient
  - No blur effects
  - Simple shadows
```

### Inconsistent Input Styling
```
Landing Page Form (ContactSalesDialog):
  - rounded-lg border-gray-300
  - focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20
  - Standard Bootstrap-like styling

Main App doesn't use common input components
  - Inputs embedded in dashboard cards
  - Consistent with app aesthetic
```

---

## Part 6: Missing Design System Elements

### What the App Lacks Compared to Landing:

1. **Visual Hierarchy**: Landing uses size, color, and effects; app is flat
2. **Branding Integration**: Landing features Fizko branding throughout; app is minimal
3. **Micro-interactions**: Landing has interactive elements; app is utilitarian
4. **Decorative Elements**: Landing uses blobs, gradients, icons; app is text/data focused
5. **Premium Feel**: Landing appears enterprise-grade; app feels minimal
6. **Color Identity**: Landing establishes blue/purple identity; app uses neutrals
7. **Gradient System**: Landing uses extensively; app almost never uses them

---

## Part 7: Recommendations for Consistency

### Option 1: Elevate the App to Landing Standards
- Add gradient backgrounds to main dashboard
- Implement rounded-3xl corners on cards
- Use backdrop-blur effects
- Scale up typography
- Add decorative animated elements
- Risk: May reduce data visibility

### Option 2: Simplify Landing to Match App
- Replace gradients with solid colors
- Reduce animation complexity
- Use app's color scheme (slate/emerald)
- Standardize border radius to rounded-lg
- Remove decorative elements
- Risk: May reduce marketing appeal

### Option 3: Create Unified Design System
- Define two tiers: "Marketing" and "App" components
- Use a consistent color palette (blue/purple + emerald)
- Establish animation guidelines (micro-interactions vs. premium effects)
- Create component library with variants for each context
- Recommend: Most professional approach

---

## Summary Table

```
Feature                 | Landing Page          | Main App              | Recommendation
------------------------|----------------------|----------------------|------------------
Primary Color Scheme    | Blue-Purple          | Slate-Emerald        | Unify to blue-purple
Font Sizing             | Large (4xl-5xl)      | Standard (2xl-3xl)    | Moderate between
Border Radius           | Large (3xl)          | Standard (lg-xl)      | medium (2xl)
Shadows                 | Heavy (xl-2xl)       | Light (sm-none)       | Medium (md)
Gradients               | Extensive            | Minimal               | Moderate (data cards)
Animations              | Complex              | Minimal               | Subtle micro-interactions
Button Styling          | Gradient rounded-full| Solid rounded-md      | Create variant system
Card Styling            | Gradient with blur   | Solid with border     | Subtle gradient
Dark Mode               | Full support         | Full support          | Maintain consistency
```

---

## Files Referenced

### Landing Page
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/pages/home/ui/Landing.tsx`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/pages/home/ui/ContactSalesDialog.tsx`

### Main Application
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/features/dashboard/ui/Home.tsx`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/features/dashboard/ui/TaxSummaryCard.tsx`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/features/dashboard/ui/CompanyInfoCard.tsx`

### Configuration & Styles
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/tailwind.config.ts`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/app/styles/index.css`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/app/styles/chateable.css`

### Component Library
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/shared/components/ui/button.tsx`
- `/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/frontend/src/shared/components/ui/card.tsx`

