# Experiment Copilot — Demo Script

Golden-path walkthrough for the hackathon demo. There is **one experiment** in chat (`exp_1`); the storefront exposes **four variation presets** (control A vs treatment B UI diffs).

| Role | Where |
|------|--------|
| **Experiment** | Dashboard chat + DB — hypothesis, simulate, analyze, verdict |
| **Variation** | Storefront URL — which funnel surface differs (`?variation=…&variant=A\|B`) |

---

## Before you start

### 1. Start the stack

```bash
docker compose up -d --build
```

Wait until:

- Storefront: [http://localhost:5173](http://localhost:5173)
- PM dashboard: [http://localhost:5174](http://localhost:5174)
- Copilot API logs show Playwright tools loaded (optional, for browser inspect)

Ensure `packages/copilot-backend/.env` contains a valid `OPENAI_API_KEY`.

### 2. Open the dashboard

Go to [http://localhost:5174](http://localhost:5174).

Use the **Storefront variation** dropdown in the header to pick which A/B UI preset you are demoing. Switching a variation updates:

- Inspect URLs on the experiment row
- Hypothesis + control/treatment names in the Experiment drawer
- Default simulate conversion rates

### 3. Reset demo data (clean slate)

1. Click **Experiment** (top right).
2. Under **Demo reset**, choose scenario **Scale — B wins**.
3. Click **Reset demo**.

This seeds a single `exp_1` row with URLs for the currently selected variation and clears events/chat.

---

## Demo flow (recommended order)

Run each variation as a **mini story**: preview A/B → simulate traffic → analyze → show verdict.

| # | Variation | Primary metric (agent should infer) | Scale scenario verdict |
|---|-----------|-------------------------------------|-------------------------|
| 1 | Checkout CTA | `checkout_completed` | **Scale** (B wins) |
| 2 | PLP Social Proof | `add_to_cart` | **Scale** (B wins) |
| 3 | PDP Sticky CTA | `add_to_cart` | **Scale** (B wins) |
| 4 | Cart Shipping Nudge | `checkout_started` | **Rollback** (A wins — default rates are 22% / 19.5%) |

> **Note:** Reset only clears metadata and rewrites URLs; you must **Simulate traffic** after every reset. The scenario dropdown labels expected outcomes for checkout-cta; other variations use their own default conversion rates in the simulate panel (auto-filled when you switch the variation dropdown).

---

## Variation 1 — Checkout CTA Redesign

**Hypothesis:** Redesigned checkout CTA increases purchase completion.

**What differs**

| Control (A) | Treatment (B) |
|-------------|----------------|
| Plain “Place Order” button | Hero green CTA, urgency copy, trust badge |

### Preview in browser

Open from **Experiment drawer → Inspect in browser**, or paste:

- Control: [http://localhost:5173/?variation=checkout-cta&variant=A&screen=checkout](http://localhost:5173/?variation=checkout-cta&variant=A&screen=checkout)
- Treatment: [http://localhost:5173/?variation=checkout-cta&variant=B&screen=checkout](http://localhost:5173/?variation=checkout-cta&variant=B&screen=checkout)

**Say:** “The only difference is the checkout CTA — listing, PDP, and cart are identical. The agent inspects these URLs and infers `checkout_completed` as the success metric.”

### Dashboard steps

1. Header dropdown → **Checkout CTA Redesign**
2. **Experiment** → **Simulate traffic** (defaults ~15.8% A / 18% B, 500+ users)
3. Confirm metrics table shows all funnel events; `checkout_completed` differs by variant
4. **Run full analysis** (URLs prefilled) or chat:

   > Analyze this experiment. Here are the variant URLs:  
   > A: http://localhost:5173/?variation=checkout-cta&variant=A&screen=checkout  
   > B: http://localhost:5173/?variation=checkout-cta&variant=B&screen=checkout

5. **Expected:** Verdict **Scale** — B’s checkout conversion is significantly higher

### Optional CLI smoke test

```bash
curl.exe -s -X POST "http://localhost:3001/experiments/exp_1/analyze" ^
  -H "Content-Type: application/json" ^
  -d "{\"variantAUrl\":\"http://localhost:5173/?variation=checkout-cta&variant=A&screen=checkout\",\"variantBUrl\":\"http://localhost:5173/?variation=checkout-cta&variant=B&screen=checkout\"}"
```

---

## Variation 2 — PLP Social Proof

**Hypothesis:** Star ratings + review counts on product cards increase add-to-cart rate.

**What differs**

| Control (A) | Treatment (B) |
|-------------|----------------|
| Product cards without ratings | Star ratings + review count on each card |

### Preview in browser

- Control: [http://localhost:5173/?variation=plp-social-proof&variant=A](http://localhost:5173/?variation=plp-social-proof&variant=A)
- Treatment: [http://localhost:5173/?variation=plp-social-proof&variant=B](http://localhost:5173/?variation=plp-social-proof&variant=B)

**Say:** “This tests top-of-funnel social proof on the product listing. Same experiment in chat — different `variation` param in the URL.”

### Dashboard steps

1. Header dropdown → **PLP Social Proof** (URLs + hypothesis update automatically)
2. **Reset demo** (Scale) if switching from another variation
3. **Simulate traffic** (~12% A / 14.5% B)
4. **Run full analysis**

5. **Expected:** Agent infers **`add_to_cart`** (not checkout), verdict **Scale**

**Talking point:** Event matrix still shows `page_view`, `add_to_cart`, `checkout_started`, `checkout_completed` — the agent picks the metric that matches the UI diff.

---

## Variation 3 — PDP Sticky CTA

**Hypothesis:** A sticky bottom add-to-cart bar on product detail increases add-to-cart rate.

**What differs**

| Control (A) | Treatment (B) |
|-------------|----------------|
| Inline “Add to Cart” only | Sticky bottom bar with prominent CTA + “Free Returns” |

### Preview in browser

- Control: [http://localhost:5173/?variation=pdp-sticky-cta&variant=A&screen=detail&product=p1](http://localhost:5173/?variation=pdp-sticky-cta&variant=A&screen=detail&product=p1)
- Treatment: [http://localhost:5173/?variation=pdp-sticky-cta&variant=B&screen=detail&product=p1](http://localhost:5173/?variation=pdp-sticky-cta&variant=B&screen=detail&product=p1)

(Product `p1` = Wireless Headphones)

### Dashboard steps

1. Header dropdown → **PDP Sticky CTA**
2. **Reset demo** → **Simulate** (~14% A / 16.5% B)
3. **Run full analysis**

4. **Expected:** Metric **`add_to_cart`**, verdict **Scale**

**Say:** “Deep links jump straight to the PDP so Playwright doesn’t have to click through the funnel.”

---

## Variation 4 — Cart Free-Shipping Nudge

**Hypothesis:** Free-shipping progress bar nudges users from cart into checkout.

**What differs**

| Control (A) | Treatment (B) |
|-------------|----------------|
| Standard cart | “Add $X more for free shipping” progress bar + emphasized checkout CTA |

### Preview in browser

Uses Phone Stand (`p8`, $24.99) so the progress bar is visible (below $50 threshold):

- Control: [http://localhost:5173/?variation=cart-shipping-nudge&variant=A&screen=cart&product=p8](http://localhost:5173/?variation=cart-shipping-nudge&variant=A&screen=cart&product=p8)
- Treatment: [http://localhost:5173/?variation=cart-shipping-nudge&variant=B&screen=cart&product=p8](http://localhost:5173/?variation=cart-shipping-nudge&variant=B&screen=cart&product=p8)

### Dashboard steps

1. Header dropdown → **Cart Free-Shipping Nudge**
2. **Reset demo** (any scenario) — clears events and re-seeds experiment metadata
3. Confirm simulate panel shows **22.0% A / 19.5% B** (auto-filled for this variation)
4. **Simulate traffic** with **5000** users (recommended for a significant result)
5. **Run full analysis**

6. **Expected:** Metric **`checkout_started`**, verdict **Rollback** (control cart wins — B’s nudge underperforms at default rates)

**Say:** “Not every test is a winner — this one shows the agent recommending rollback when B underperforms.”

---

## Full golden path (5 minutes, one variation)

Fastest single demo using **Checkout CTA**:

1. `docker compose up -d --build`
2. Open [localhost:5174](http://localhost:5174)
3. Variation → **Checkout CTA Redesign**
4. Experiment drawer → Reset (**Scale**) → Simulate **5000** users
5. Click **Run full analysis**
6. Show decision card → **Apply** (Scale → 100% B traffic)

Chat line if not using one-click analyze:

> We redesigned the checkout button in variant B. Should we scale it?

---

## Other demo scenarios (Experiment drawer)

| Scenario | Use when |
|----------|----------|
| **Continue — low sample** | Show “need more data” verdict (100 users) |
| **Stop — no winner** | A ≈ B, not significant |
| **Rollback — B loses** | Flip default rates; B underperforms |
| **Empty — just launched** | No events; agent asks for data or continues |

---

## Architecture talking points

1. **Metric is inferred, not configured** — `primary_metric` is NULL; agent discovers events via SQL and picks the metric from the page diff.
2. **Numbers are deterministic** — z-test and Scale/Continue/Stop/Rollback rules live in code, not the LLM.
3. **URLs use `variation`, not experiment ids** — experiment identity stays in chat/DB; storefront is a reusable A/B surface catalog.
4. **One telemetry table** — all events flow to `universal_events`; simulate emits the full funnel so any variation is analyzable.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Dashboard 500 on analyze | Check `OPENAI_API_KEY` in `packages/copilot-backend/.env` |
| Stale metrics after reset | Experiment drawer → Reset demo, then Simulate again |
| Old URLs with `?experiment=exp_2` | Run **Reset demo** to rewrite URLs to `?variation=…` |
| Playwright inspect fails | Agent falls back to chat-only; paste variant URLs manually |
| Wrong metric inferred | Re-run after simulate; confirm event matrix has data for all event names |

### Reset events manually (optional)

```bash
docker compose exec -T ecom-backend python -c "import psycopg; from app.config import ADMIN_DATABASE_URL; c=psycopg.connect(ADMIN_DATABASE_URL, autocommit=True); c.execute('TRUNCATE universal_events RESTART IDENTITY'); print('events cleared')"
docker compose exec -T ecom-backend python scripts/seed.py
```

---

## URL cheat sheet

```
Checkout:  ?variation=checkout-cta&variant={A|B}&screen=checkout
PLP:       ?variation=plp-social-proof&variant={A|B}
PDP:       ?variation=pdp-sticky-cta&variant={A|B}&screen=detail&product=p1
Cart:      ?variation=cart-shipping-nudge&variant={A|B}&screen=cart&product=p8
Legacy:    ?variant={A|B}&screen=checkout   (defaults to checkout-cta)
```
