# How to Deploy the Web App (GitHub Pages)

The keyboard recommender is a single HTML file — no build step, no server, no
framework. It can be deployed anywhere static files are served.

## Option 1: GitHub Pages (recommended)

### Automatic (just push)

1. Go to your repo on GitHub
2. Settings > Pages
3. Source: "Deploy from a branch"
4. Branch: `main`, folder: `/web`
5. Save

Your app will be live at:
`https://urikkkk.github.io/keyboard-shopping-agent/keyboard_finder.html`

### Alternative: root deployment

If you want it at the root URL, copy the HTML to the repo root:

```bash
cp web/keyboard_finder.html index.html
git add index.html && git commit -m "Add root index for GitHub Pages"
git push
```

Then set Pages source to `/` (root).

## Option 2: Netlify (drag and drop)

1. Go to [netlify.com](https://www.netlify.com/)
2. Drag the `web/` folder onto the Netlify dashboard
3. Done — you get a URL immediately

## Option 3: Any static host

The web app is fully self-contained. Upload `keyboard_finder.html` to:
- Vercel
- Cloudflare Pages
- AWS S3 + CloudFront
- Any web server (nginx, Apache, Caddy)

## Updating the data

The web app has product data embedded directly in the HTML. To update:

1. Run the pipeline to generate fresh data
2. The pipeline outputs `output/keyboards.csv`
3. To regenerate the web app with fresh data, you can copy the CSV into
   the HTML's JavaScript data section, or build a version that fetches
   the CSV at runtime (see `web/keyboard_finder.html` for the data format)

## Customizing the web app

The web app is vanilla HTML + CSS + JavaScript. Edit `web/keyboard_finder.html`
directly:

- **Colors**: Change CSS variables in `:root { ... }`
- **Filters**: Add/remove filter dropdowns in the `#filters` section
- **Card layout**: Modify the `renderGrid()` function
- **Scoring display**: Adjust the score bar and stat display
