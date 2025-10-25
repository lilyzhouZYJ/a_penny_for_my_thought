import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        claude: {
          bg: "hsl(var(--claude-bg))",
          sidebar: "hsl(var(--claude-sidebar))",
          border: "hsl(var(--claude-border))",
          text: "hsl(var(--claude-text))",
          "text-muted": "hsl(var(--claude-text-muted))",
          accent: "hsl(var(--claude-accent))",
          hover: "hsl(var(--claude-hover))",
          "user-message": "hsl(var(--claude-user-message))",
          "assistant-message": "hsl(var(--claude-assistant-message))",
          "warm-accent": "hsl(var(--claude-warm-accent))",
          "light-accent": "hsl(var(--claude-light-accent))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        serif: ['var(--font-crimson-pro)', 'Crimson Pro', 'Georgia', 'serif'],
        sans: ['var(--font-crimson-pro)', 'Crimson Pro', 'Georgia', 'serif'],
      },
      fontSize: {
        'xs': ['0.9375rem', { lineHeight: '1.25rem' }], // 15px (was 14px)
        'sm': ['1.0625rem', { lineHeight: '1.5rem' }],   // 17px (was 16px)
        'base': ['1.1875rem', { lineHeight: '1.75rem' }], // 19px (was 18px)
        'lg': ['1.3125rem', { lineHeight: '1.875rem' }], // 21px (was 20px)
        'xl': ['1.4375rem', { lineHeight: '2rem' }],     // 23px (was 22px)
        '2xl': ['1.6875rem', { lineHeight: '2.25rem' }], // 27px (was 26px)
        '3xl': ['1.9375rem', { lineHeight: '2.5rem' }], // 31px (was 30px)
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
    },
  },
  plugins: [require("tailwindcss-animate"), require("@tailwindcss/typography")],
} 

export default config


