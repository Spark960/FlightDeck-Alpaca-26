/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Pure brutalist palette
        ink:     "#000000",
        paper:   "#FFFFFF",
        void:    "#0A0A0A",  // near-black page bg
        slab:    "#111111",  // panel bg
        rule:    "#FFFFFF",  // border color
        rule2:   "#333333",  // secondary border
        muted:   "#666666",

        // Single electric accent — yellow
        y:       "#FFE500",   // ELECTRIC YELLOW — the ONLY decoration
        pos:     "#00FF41",   // terminal green — profit
        neg:     "#FF003C",   // terminal red — loss
        warn:    "#FF8C00",   // amber — caution
        info:    "#00BFFF",   // cold blue — AI/info
        violet:  "#BF00FF",   // purple — AI events
      },
      fontFamily: {
        sans: ["Space Mono", "Courier New", "monospace"],
        mono: ["Space Mono", "Courier New", "monospace"],
      },
      borderWidth: {
        DEFAULT: "2px",
        thick:   "3px",
      },
      boxShadow: {
        // Hard offset — the brutalist signature
        hard:   "4px 4px 0 #FFFFFF",
        "hard-y":"4px 4px 0 #FFE500",
        "hard-g":"4px 4px 0 #00FF41",
        "hard-r":"4px 4px 0 #FF003C",
        "hard-sm":"2px 2px 0 #FFFFFF",
      },
      maxWidth: {
        desktop: "1440px",
      },
    },
  },
  plugins: [],
};
