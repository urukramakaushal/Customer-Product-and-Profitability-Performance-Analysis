# Executive Summary

## Customer, Product and Profitability Performance Analysis — APL Logistics

**Prepared for:** Commercial leadership and government stakeholders
**Scope:** 180,519 order lines, 40 fields, 20,261 customers, 164 countries
**Purpose:** Margin intelligence — establishing where the business creates and destroys value

---

### The headline

APL Logistics converts **$35.21M of gross sales into $3.81M of profit** — a 12.03% margin. Between those two numbers sit two leaks of almost equal size:

- **$3.57M given away in discounts** — 94 cents for every dollar of profit retained
- **$3.71M lost on unprofitable orders** — 18.7% of all order lines, erasing 49% of the profit earned on everything else

The business generates $7.51M of gross profit and keeps $3.81M. Roughly half is consumed before it reaches the bottom line.

---

### Four findings that matter

**1. Discounting is a straight margin giveaway with no volume return.**
Average units per order is 2.13 at *every* discount level, from 0% to 25%. The correlation between discount depth and order size is zero. Yet margin on gross sales falls steadily from 13.0% at no discount to 9.6% in the deepest band, and profit per order drops 26%. Deeper discounts buy nothing and cost 3.4 margin points.

**2. Standard margin reporting hides this completely.**
Margin measured on invoiced revenue is flat at ~12% across every discount band, because the discount shrinks the denominator alongside the numerator. Only margin measured on *gross* sales reveals the erosion. This is a definitional change, not a system change.

**3. The loss-making tail is uniform, not concentrated.**
18.7% of orders lose money — and that rate holds between 18.3% and 19.0% in every market, every customer segment, every price band and every discount level. There is no bad region, bad segment or bad product line to fix. This is a cost-structure problem, and diagnosing it requires cost data the current extract does not contain.

**4. Revenue is concentrated in ten products.**
The top 10 of 118 products generate 90% of revenue; the top 5 generate 61%. This is a real and significant dependency exposure, independent of any margin consideration.

---

### An important caution on customer rankings

Conventional analysis of this data produces a bottom customer quintile of 4,052 accounts losing $1.05M, and the standard recommendation to de-prioritise them.

**We tested whether that ranking is stable, and it is not.** Splitting each product's orders randomly in half and comparing margin between the halves returns a correlation of **−0.29** — a product's realised margin carries no information about its own margin. For customers the figure is +0.16, barely above noise.

The bottom-tier customers also do not behave like low-value accounts: they place **8.3 orders at $208 average value**, compared with the top tier's 17.0 orders at $225. They order more often than the middle tiers and at comparable size. Their tier placement comes from margin variation, not from buying less.

Acting on that ranking would forfeit **$6.18M of revenue — 19.5% of the book** — with no defensible expectation of margin gain. We recommend against it.

---

### Recommended actions

| Priority | Action | Modelled impact |
|---|---|---|
| 1 | Cap discretionary discounting at 10%, with approval required above | **+28.5% profit** at fixed demand ($1.09M recovered) — pilot first |
| 2 | Report margin on gross sales, not net revenue | No cost; makes the erosion visible to every decision-maker |
| 3 | Obtain cost decomposition (freight, handling, returns) to diagnose the loss tail | Addresses the largest single leak, currently undiagnosable |
| 4 | **Do not** cull the bottom customer quintile | Protects $6.18M of revenue |
| 5 | Manage the 10-product revenue concentration as a supply-risk item | Dependency exposure, not a margin issue |
| 6 | Add order date to the data extract | Unlocks all trend, seasonality and lifetime-value analysis |

Discount cap scenarios, holding demand fixed: a 15% cap recovers $401K (+10.5%), a 10% cap $1.09M (+28.5%), a 5% cap $2.10M (+55.2%). These are upper bounds. The measured zero volume elasticity makes fixed demand a reasonable starting assumption, but a pilot on a defined subset of accounts should precede any book-wide rollout.

---

### What this analysis can and cannot support

**It establishes** the size and composition of the margin gap, the scale of discount erosion and its lack of volume return, revenue and profit concentration, and the uniformity of the loss-making tail.

**It does not establish** which individual customers or products are genuinely unprofitable. Testing showed that entity-level margin in this dataset does not replicate across an entity's own orders — it varies independently of price, quantity, discount, market, segment, category and shipping mode. Aggregate financial facts are sound; rankings of individual customers and products are not, and this report does not offer them as a basis for action.

**Two gaps limit the work materially.** The extract contains no order date, so no trend, seasonality or customer-lifetime analysis is possible. It contains no cost breakdown, so the largest profit leak cannot be traced to its source. Closing these two gaps would deliver more value than further analysis of the current data.

---

### Accompanying deliverables

- **Research paper** — validation methodology, full findings, reliability testing, limitations
- **Streamlit dashboard** — five modules with cascading filters for segment, market, region, category, product, discount rate and shipping mode; interactive discount-cap what-if modelling; exportable customer and product tables
