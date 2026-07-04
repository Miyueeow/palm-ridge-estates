# Palm Ridge Estates — Lot Finder API

A tiny serverless function that powers the "Ask the Lot Finder" feature on the
[Palm Ridge Estates map](https://miyueeow.github.io/palm-ridge-estates/).
Deployed separately from the static site so the API key never touches the
browser.

**Note:** this uses [Groq](https://groq.com) — a fast inference provider for
open-source models (Llama 3.x) — not Anthropic's Claude. Groq's API is
OpenAI-compatible and has a generous free tier, which is why it's used here.
If you want the real Claude API instead, see the "Switching to Claude"
section at the bottom.

## How it works

1. The map sends a POST request with `{ query, lots }` (the buyer's natural-
   language request + the currently available lots)
2. This function calls the model with that data and a system prompt asking
   it to pick the best-matching lots
3. The response is parsed and returned as `{ matches: [...], explanation: "..." }`
4. The map highlights the returned `matches` on screen

## Deploy to Vercel

### 1. Install the Vercel CLI (one-time)
```bash
npm install -g vercel
```

### 2. Log in
```bash
vercel login
```

### 3. Deploy from this folder
```bash
cd palm-ridge-api
vercel
```
Follow the prompts (accepting defaults is fine for a first deploy).

### 4. Get a Groq API key
Go to **[console.groq.com](https://console.groq.com)** -> sign up/log in ->
**API Keys** -> **Create API Key**. Copy it immediately.

### 5. Add your API key as an environment variable
Either via the CLI:
```bash
vercel env add GROQ_API_KEY
```
paste your key when prompted, select all environments (Production, Preview, Development).

Or via the Vercel dashboard: your project -> **Settings -> Environment Variables** ->
add `GROQ_API_KEY` with your key as the value.

### 6. Deploy to production
```bash
vercel --prod
```
Vercel will give you a URL like:
```
https://palm-ridge-api.vercel.app
```
Your live endpoint is:
```
https://palm-ridge-api.vercel.app/api/lot-finder
```

### 7. Lock down CORS (recommended once you have your real domain)
In `api/lot-finder.js`, change:
```js
res.setHeader("Access-Control-Allow-Origin", "*");
```
to:
```js
res.setHeader("Access-Control-Allow-Origin", "https://miyueeow.github.io");
```
Then redeploy with `vercel --prod`. This stops other sites from using your
API key through your endpoint.

## Local testing

```bash
vercel dev
```
This runs the function locally (reads `.env.local` — copy `.env.example` to
`.env.local` and fill in your key first).

Test it directly:
```bash
curl -X POST http://localhost:3000/api/lot-finder \
  -H "Content-Type: application/json" \
  -d '{"query":"3 bedroom corner lot under 3M", "lots":[{"lot_id":"LOT-0001","bedrooms":3,"area_sqm":120,"price_php":2500000,"lot_type":"corner","distance_to_entrance_m":50,"phase":1}]}'
```

## Cost note

This uses `llama-3.3-70b-versatile` on Groq's free tier, which is generous
enough for a low-traffic portfolio demo. Check
[console.groq.com](https://console.groq.com) for current rate limits.

## Switching to Claude

If you'd rather use the real Claude API instead of Groq, the swap is small —
change the `fetch` call to hit `https://api.anthropic.com/v1/messages` with
an `x-api-key` header and `anthropic-version` header instead of `Authorization:
Bearer`, and use a model like `claude-haiku-4-5-20251001`. Ask your AI
assistant to walk you through this rewrite if you want to make that change
later — it only touches `api/lot-finder.js`.
