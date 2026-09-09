# Customer, Product & Profitability Performance Analysis — APL Logistics

Margin intelligence on 180,519 supply-chain order lines: where value is created and where it leaks.

## Contents

| File | Description |
|---|---|
| `app.py` | Streamlit dashboard (5 modules, 7 cascading filters, discount what-if) |
| `research_paper.md` | Full paper: validation, findings, reliability testing, recommendations |
| `executive_summary.md` | Summary for commercial leadership and government stakeholders |
| `requirements.txt` | Python dependencies |

## Running the dashboard

```bash
pip install -r requirements.txt
# place the dataset next to app.py, named APL_Logistics.csv
streamlit run app.py
```

## Dashboard modules

1. **Revenue & Profit Overview** — KPIs, profit-destruction waterfall, Pareto concentration curves
2. **Customer Value** — value tiers with behavioural comparison, top/bottom customers, segment contribution
3. **Product & Category** — revenue-vs-margin bubble plot, category heatmaps, loss flagging
4. **Discount Impact Analyzer** — discount-band economics, elasticity correlations, interactive cap what-if
5. **Market & Region** — market/region/country profitability with margin-spread interpretation

Filters: customer segment, market, order region, category, product, discount-rate range, shipping mode.

## Headline results

- Gross sales **$35.21M** → revenue **$31.64M** → profit **$3.81M** (12.03% margin)
- Discounts: **$3.57M** — $0.94 given away per $1 of profit retained
- **18.7%** of order lines lose money, destroying **$3.71M** — 49% of gross profit
- Discount buys no volume: units/order is 2.13 at every discount level; correlation +0.000
- Margin on gross sales falls **13.0% → 9.6%** as discount deepens
- 10% discount cap models to **+28.5% profit** (fixed demand)
- Top 10 of 118 products = **90%** of revenue
- Top 20% of customers = **79%** of profit

## Two caveats that shape the conclusions

**Entity-level margin does not replicate.** A split-half reliability test returns −0.29 across products and +0.16 across customers, and mean profit ratio is flat across every market, segment, category, price band and discount band. Aggregate financials are sound; rankings of individual customers and products are not, and the paper does not offer them as a basis for action.

**No order date field.** Trend, seasonality and lifetime-value analysis are impossible on this extract. The dashboard substitutes discount-level, price-band and cumulative-contribution trends.
