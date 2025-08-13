/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        tdv: {
          primary: '#821417',
          secondary: '#bd4c42',
          accent: '#fa8072',
          light: '#fff4e1',
          muted: '#ffbba8'
        }
      }
    },
  },
  plugins: [],
}