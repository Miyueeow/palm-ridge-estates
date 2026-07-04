// api/lot-finder.js
//
// Vercel serverless function. Receives a natural-language query plus the
// current pool of available lots, asks an LLM (via Groq) to rank the best
// matches, and returns a short explanation + the matching lot_ids.
//
// The API key lives only here (as a Vercel environment variable), never
// in the browser, so it's safe to call this from a public static site.
//
// Uses Groq (https://groq.com) — an OpenAI-compatible API serving fast
// open-source models (Llama 3.x here). This is NOT Anthropic's Claude;
// swap this file for the Claude version if you want the real Claude API.

export default async function handler(req, res) {
  // --- CORS: allow your GitHub Pages site to call this function ---
  res.setHeader("Access-Control-Allow-Origin", "https://miyueeow.github.io");// tighten to your exact domain once live, see README
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    res.status(200).end();
    return;
  }

  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  try {
    const { query, lots } = req.body;

    if (!query || !Array.isArray(lots)) {
      res.status(400).json({ error: "Expected { query: string, lots: array }" });
      return;
    }

    // Trim the lot data down to only what the model needs — keeps the
    // request small and cheap, and avoids leaking unrelated fields.
    const compactLots = lots.map(l => ({
      lot_id: l.lot_id,
      bedrooms: l.bedrooms,
      area_sqm: l.area_sqm,
      price_php: l.price_php,
      lot_type: l.lot_type,
      distance_to_entrance_m: l.distance_to_entrance_m,
      phase: l.phase,
    }));

    const systemPrompt = `You are a helpful real estate assistant for "Palm Ridge Estates," a residential subdivision. You'll be given a buyer's natural-language request and a list of currently available lots as JSON. Pick the best-matching lots (up to 4) and explain briefly why each fits.

Respond ONLY with valid JSON in this exact shape, nothing else:
{
  "matches": ["LOT-0001", "LOT-0002"],
  "explanation": "One short paragraph explaining the picks in plain, friendly language."
}
If nothing matches well, return an empty matches array and explain what's close instead.`;

    const userMessage = `Buyer request: "${query}"\n\nAvailable lots:\n${JSON.stringify(compactLots)}`;

    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${process.env.GROQ_API_KEY}`,
      },
      body: JSON.stringify({
        model: "llama-3.3-70b-versatile",
        max_tokens: 500,
        response_format: { type: "json_object" },
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: userMessage },
        ],
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error("Groq API error:", errText);
      res.status(502).json({ error: "Upstream API error" });
      return;
    }

    const data = await response.json();
    const rawText = data.choices?.[0]?.message?.content;

    let parsed;
    try {
      const cleaned = (rawText || "").replace(/```json|```/g, "").trim();
      parsed = JSON.parse(cleaned);
    } catch (e) {
      console.error("Failed to parse model output:", rawText);
      res.status(502).json({ error: "Could not parse model response" });
      return;
    }

    res.status(200).json(parsed);
  } catch (err) {
    console.error("Handler error:", err);
    res.status(500).json({ error: "Internal server error" });
  }
}
