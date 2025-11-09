// Professional button base styles
export const buttonBase =
    'inline-flex items-center justify-center rounded-xl font-semibold tracking-tight transition-all duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 active:scale-95'

// Primary CTA - Brand color with strong presence
export const primaryButton = `${buttonBase} border border-transparent bg-brand-600 px-5 py-2.5 text-sm text-white shadow-sm hover:bg-brand-700 focus-visible:outline-brand-600 disabled:opacity-50 disabled:cursor-not-allowed`

// Secondary - Outline style for less prominent actions
export const secondaryButton = `${buttonBase} border border-neutral-300 bg-white px-5 py-2.5 text-sm text-neutral-700 hover:bg-neutral-50 hover:border-neutral-400 focus-visible:outline-neutral-600`

// Ghost - Minimal style for tertiary actions
export const ghostButton = `${buttonBase} border border-transparent px-5 py-2.5 text-sm text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900 focus-visible:outline-neutral-600`

// Accent - For special promotions or highlights
export const accentButton = `${buttonBase} border border-transparent bg-accent px-5 py-2.5 text-sm text-white shadow-sm hover:bg-accent-dark focus-visible:outline-accent disabled:opacity-50 disabled:cursor-not-allowed`

// Danger - For destructive actions
export const dangerButton = `${buttonBase} border border-transparent bg-error-600 px-5 py-2.5 text-sm text-white shadow-sm hover:bg-error-700 focus-visible:outline-error-600 disabled:opacity-50 disabled:cursor-not-allowed`

