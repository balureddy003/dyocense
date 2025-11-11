// Modern SaaS button base styles
export const buttonBase =
    'inline-flex items-center justify-center rounded-xl font-semibold tracking-tight transition-all duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 active:scale-[0.98]'

// Primary CTA - Gradient brand with glow effect
export const primaryButton = `${buttonBase} btn-gradient border-0 px-6 py-3 text-sm text-white disabled:opacity-50 disabled:cursor-not-allowed`

// Secondary - Outline style with brand color
export const secondaryButton = `${buttonBase} border-2 border-brand-500 bg-white px-6 py-3 text-sm text-brand-600 hover:bg-brand-50 hover:border-brand-600 focus-visible:outline-brand-500 shadow-sm`

// Ghost - Minimal style for tertiary actions
export const ghostButton = `${buttonBase} border border-transparent px-5 py-2.5 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900 focus-visible:outline-gray-600`

// Accent - For special promotions or highlights
export const accentButton = `${buttonBase} border border-transparent bg-violet-500 px-6 py-3 text-sm text-white shadow-md hover:bg-violet-600 hover:shadow-lg focus-visible:outline-violet-500 disabled:opacity-50 disabled:cursor-not-allowed`

// Danger - For destructive actions
export const dangerButton = `${buttonBase} border border-transparent bg-red-500 px-6 py-3 text-sm text-white shadow-sm hover:bg-red-600 focus-visible:outline-red-500 disabled:opacity-50 disabled:cursor-not-allowed`

