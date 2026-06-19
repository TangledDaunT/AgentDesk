/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        void: {
          DEFAULT: '#0A0E14',
          surface: '#10151D',
          raised: '#161C26',
          line: '#1F2733'
        },
        signal: {
          DEFAULT: '#5EEAD4',
          dim: '#2D5F58',
          bright: '#99F6E4'
        },
        amber: {
          DEFAULT: '#F5A623',
          dim: '#6B4A18'
        },
        violet: {
          DEFAULT: '#7C7AED',
          deep: '#312E81',
          dim: '#2A2860'
        },
        slate: {
          idle: '#475569',
          text: '#E2E8F0',
          muted: '#8B96A5',
          faint: '#5B6573'
        },
        danger: {
          DEFAULT: '#F0654A'
        }
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace']
      },
      animation: {
        'pulse-slow': 'pulse-slow 2.4s ease-in-out infinite',
        'pulse-fast': 'pulse-fast 1s ease-in-out infinite',
        scan: 'scan 3s linear infinite',
        'fade-up': 'fade-up 0.4s ease-out'
      },
      keyframes: {
        'pulse-slow': {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.4 }
        },
        'pulse-fast': {
          '0%, 100%': { opacity: 1, transform: 'scale(1)' },
          '50%': { opacity: 0.6, transform: 'scale(1.15)' }
        },
        scan: {
          '0%': { backgroundPosition: '0% 0%' },
          '100%': { backgroundPosition: '0% 200%' }
        },
        'fade-up': {
          '0%': { opacity: 0, transform: 'translateY(8px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' }
        }
      }
    }
  },
  plugins: []
}
