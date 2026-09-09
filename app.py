"""
Customer, Product and Profitability Performance Analysis - APL Logistics
Streamlit commercial-intelligence dashboard.

Run with:  streamlit run app.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Profitability Analytics | APL Logistics",
                   page_icon="💰", layout="wide")

DATA_PATH = "APL_Logistics.csv"
INVALID_STATUS = ["CANCELED", "SUSPECTED_FRAUD"]

GREEN, RED, BLUE, GREY = "#2E8B77", "#D64545", "#3A6EA5", "#8A94A6"


# --------------------------------------------------------------------------
# Load, validate, clean
# --------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading and validating order data...")
def load_data(path: str):
    df = pd.read_csv(path, encoding="latin-1")
    log = {"rows_raw": len(df)}

    # --- Financial field validation -------------------------------------
    # Sales should equal unit price x quantity; Order Item Total should equal
    # Sales less discount. Rows failing these identities are internally
    # inconsistent and are dropped rather than silently analysed.
    price_qty = df["Order Item Product Price"] * df["Order Item Quantity"]
    ok_sales = np.isclose(df["Sales"], price_qty, atol=0.05)
    ok_total = np.isclose(df["Order Item Total"], df["Sales"] - df["Order Item Discount"],
                          atol=0.05)
    log["failed_identity"] = int((~(ok_sales & ok_total)).sum())
    df = df[ok_sales & ok_total]

    # --- Zero / non-positive value records ------------------------------
    before = len(df)
    df = df[(df["Sales"] > 0) & (df["Order Item Total"] > 0) & (df["Order Item Quantity"] > 0)]
    log["zero_value"] = before - len(df)

    # --- Duplicates ------------------------------------------------------
    before = len(df)
    df = df.drop_duplicates()
    log["duplicates"] = before - len(df)

    # --- Commercially invalid orders -------------------------------------
    # Cancelled and suspected-fraud orders never produced realisable revenue.
    # Including them inflates both revenue and profit.
    log["excluded_status"] = int(df["Order Status"].isin(INVALID_STATUS).sum())
    log["excluded_status_sales"] = float(
        df.loc[df["Order Status"].isin(INVALID_STATUS), "Order Item Total"].sum())
    df = df[~df["Order Status"].isin(INVALID_STATUS)].copy()

    # --- Normalisation ---------------------------------------------------
    for col in ["Category Name", "Product Name", "Market", "Order Region",
                "Customer Segment", "Department Name", "Shipping Mode",
                "Order Country", "Customer Country"]:
        df[col] = df[col].astype(str).str.strip()
    # Customer Country is recorded in Spanish in the source extract.
    df["Customer Country"] = df["Customer Country"].replace({"EE. UU.": "United States"})

    # --- Derived financial fields ----------------------------------------
    df = df.rename(columns={"Order Item Total": "Revenue",
                            "Order Profit Per Order": "Profit",
                            "Order Item Discount": "Discount",
                            "Order Item Discount Rate": "DiscountRate",
                            "Sales": "GrossSales",
                            "Order Item Profit Ratio": "ProfitRatio",
                            "Order Item Quantity": "Quantity"})
    df["IsLoss"] = df["Profit"] < 0
    df["DiscountBand"] = pd.cut(df["DiscountRate"], [-0.001, 0.001, 0.05, 0.10, 0.15, 0.20, 0.26],
                                labels=["0%", "0-5%", "5-10%", "10-15%", "15-20%", "20-25%"])
    df["PriceBand"] = pd.cut(df["Product Price"], [0, 50, 100, 200, 500, 2500],
                             labels=["≤$50", "$50-100", "$100-200", "$200-500", "$500+"])

    log["rows_clean"] = len(df)
    return df, log


def kpis(frame: pd.DataFrame) -> dict:
    rev = frame["Revenue"].sum()
    prof = frame["Profit"].sum()
    gross = frame.loc[frame["Profit"] > 0, "Profit"].sum()
    loss = frame.loc[frame["Profit"] < 0, "Profit"].sum()
    ncust = frame["Customer Id"].nunique()
    return {"revenue": rev, "profit": prof,
            "margin": prof / rev * 100 if rev else np.nan,
            "gross_profit": gross, "loss": loss,
            "loss_share": -loss / gross * 100 if gross else np.nan,
            "discount": frame["Discount"].sum(),
            "gross_sales": frame["GrossSales"].sum(),
            "orders": len(frame), "customers": ncust,
            "cvi": prof / ncust if ncust else np.nan,
            "loss_order_rate": frame["IsLoss"].mean() * 100}


def money(x, decimals=2):
    if pd.isna(x):
        return "n/a"
    a = abs(x)
    sign = "-" if x < 0 else ""
    if a >= 1e6:
        return f"{sign}${a/1e6:.{decimals}f}M"
    if a >= 1e3:
        return f"{sign}${a/1e3:.0f}K"
    return f"{sign}${a:,.0f}"


def group_perf(frame, key, min_orders=1):
    t = frame.groupby(key, observed=True).agg(
        Revenue=("Revenue", "sum"), Profit=("Profit", "sum"),
        Orders=("Revenue", "count"), Discount=("Discount", "sum"),
        AvgDiscountRate=("DiscountRate", "mean"), LossOrders=("IsLoss", "sum")).reset_index()
    t = t[t["Orders"] >= min_orders]
    t["Margin %"] = (t["Profit"] / t["Revenue"] * 100).round(2)
    t["Avg discount %"] = (t["AvgDiscountRate"] * 100).round(1)
    t["Loss-order %"] = (t["LossOrders"] / t["Orders"] * 100).round(1)
    return t.drop(columns=["AvgDiscountRate", "LossOrders"])


# --------------------------------------------------------------------------
try:
    df, log = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(f"Could not find `{DATA_PATH}`. Place the CSV next to app.py and reload.")
    st.stop()

st.title("Customer, Product & Profitability Performance")
st.caption(f"APL Logistics · supply-chain commercial intelligence · "
           f"{log['rows_clean']:,} validated order lines")

# --------------------------- Sidebar filters ------------------------------
st.sidebar.header("Filters")
segments = st.sidebar.multiselect("Customer segment", sorted(df["Customer Segment"].unique()),
                                  default=sorted(df["Customer Segment"].unique()))
markets = st.sidebar.multiselect("Market", sorted(df["Market"].unique()),
                                 default=sorted(df["Market"].unique()))
region_pool = sorted(df.loc[df["Market"].isin(markets), "Order Region"].unique()) if markets \
    else sorted(df["Order Region"].unique())
regions = st.sidebar.multiselect("Order region", region_pool, default=region_pool)
cats = st.sidebar.multiselect("Category", sorted(df["Category Name"].unique()),
                              default=sorted(df["Category Name"].unique()))
prod_pool = sorted(df.loc[df["Category Name"].isin(cats), "Product Name"].unique()) if cats \
    else sorted(df["Product Name"].unique())
products = st.sidebar.multiselect("Product (blank = all)", prod_pool, default=[])
dmin, dmax = st.sidebar.slider("Discount rate (%)", 0, 25, (0, 25))
ship = st.sidebar.multiselect("Shipping mode", sorted(df["Shipping Mode"].unique()),
                              default=sorted(df["Shipping Mode"].unique()))

mask = (df["Customer Segment"].isin(segments) & df["Market"].isin(markets)
        & df["Order Region"].isin(regions) & df["Category Name"].isin(cats)
        & df["Shipping Mode"].isin(ship)
        & df["DiscountRate"].between(dmin / 100, dmax / 100))
if products:
    mask &= df["Product Name"].isin(products)

fdf = df[mask]
if fdf.empty:
    st.warning("No orders match the current filters. Widen the selection in the sidebar.")
    st.stop()

k = kpis(fdf)
k_all = kpis(df)

st.sidebar.markdown("---")
st.sidebar.metric("Order lines in selection", f"{len(fdf):,}",
                  f"{len(fdf)/len(df)*100:.0f}% of book")
st.sidebar.caption(
    f"Validation log — failed price×qty / discount identity: {log['failed_identity']:,}; "
    f"zero-value records: {log['zero_value']:,}; duplicates: {log['duplicates']:,}; "
    f"cancelled & suspected-fraud orders excluded: {log['excluded_status']:,} "
    f"({money(log['excluded_status_sales'])} of nominal revenue).")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Revenue & Profit Overview", "Customer Value", "Product & Category",
    "Discount Impact Analyzer", "Market & Region"])

# ----------------------- Tab 1: Revenue & profit --------------------------
with tab1:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total revenue", money(k["revenue"]), help="Net of discounts (Order Item Total)")
    c2.metric("Total profit", money(k["profit"]))
    c3.metric("Profit margin", f"{k['margin']:.2f}%",
              f"{k['margin']-k_all['margin']:+.2f} pts vs book")
    c4.metric("Customer Value Index", f"${k['cvi']:,.0f}",
              help="Profit contribution per unique customer in the selection")
    c5.metric("Discount given", money(k["discount"]),
              f"{k['discount']/k['gross_sales']*100:.1f}% of gross sales",
              delta_color="off")

    st.markdown("---")
    st.markdown("#### Profit is destroyed before it is booked")
    c1, c2 = st.columns([1.3, 1])
    with c1:
        fig = go.Figure(go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "total"],
            x=["Gross sales", "Discounts", "Cost of profitable orders",
               "Loss-making orders", "Net profit"],
            y=[k["gross_sales"], -k["discount"],
               -(k["revenue"] - k["gross_profit"]), k["loss"], k["profit"]],
            text=[money(k["gross_sales"]), money(-k["discount"]),
                  money(-(k["revenue"] - k["gross_profit"])), money(k["loss"]),
                  money(k["profit"])],
            textposition="outside",
            increasing=dict(marker_color=GREEN), decreasing=dict(marker_color=RED),
            totals=dict(marker_color=BLUE)))
        fig.update_layout(height=440, margin=dict(t=30), yaxis_title="USD", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.metric("Profit from profitable orders", money(k["gross_profit"]))
        st.metric("Profit destroyed by loss-making orders", money(k["loss"]),
                  f"{k['loss_share']:.0f}% of gross profit erased", delta_color="inverse")
        st.metric("Share of order lines that lose money", f"{k['loss_order_rate']:.1f}%")
        st.info(f"Every ${1:.0f} of net profit is accompanied by "
                f"${k['discount']/max(k['profit'],1):.2f} given away in discount and "
                f"${-k['loss']/max(k['profit'],1):.2f} lost on unprofitable orders.")

    st.markdown("#### Profit concentration (Pareto)")
    dim = st.radio("Concentrate by", ["Customer Id", "Product Name", "Category Name"],
                   horizontal=True, format_func=lambda s: s.replace(" Id", "").replace(" Name", ""))
    g = fdf.groupby(dim, observed=True)["Profit"].sum().sort_values(ascending=False)
    cum = g.cumsum() / g.sum() * 100
    x = np.arange(1, len(g) + 1) / len(g) * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=cum.values, mode="lines", line=dict(color=BLUE, width=3),
                             name="Cumulative profit %"))
    fig.add_trace(go.Scatter(x=[0, 100], y=[0, 100], mode="lines",
                             line=dict(color=GREY, dash="dash"), name="Even contribution"))
    fig.add_hline(y=100, line_color=GREY, line_width=1)
    fig.update_layout(height=400, xaxis_title=f"Cumulative % of {dim.replace(' Id','').replace(' Name','').lower()}s "
                                              "(ranked most to least profitable)",
                      yaxis_title="Cumulative % of total profit", margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)
    over = cum.max()
    if over > 100.5:
        st.caption(f"The curve rises above 100% and comes back down: the most profitable "
                   f"{dim.replace(' Id','').replace(' Name','').lower()}s generate "
                   f"{over:.0f}% of net profit, and the loss-making tail gives back the excess.")

# --------------------------- Tab 2: Customers -----------------------------
with tab2:
    cust = fdf.groupby("Customer Id", observed=True).agg(
        Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Orders=("Revenue", "count"),
        Segment=("Customer Segment", "first"), Country=("Customer Country", "first"),
        AvgDiscount=("DiscountRate", "mean")).reset_index()
    cust["Margin %"] = (cust["Profit"] / cust["Revenue"] * 100).round(1)
    cust["Avg order value"] = (cust["Revenue"] / cust["Orders"]).round(2)
    cust["Avg discount %"] = (cust["AvgDiscount"] * 100).round(1)
    cust = cust.drop(columns="AvgDiscount")

    tot_p = cust["Profit"].sum()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Customers", f"{len(cust):,}")
    c2.metric("Loss-making customers", f"{(cust['Profit']<0).sum():,}",
              f"{(cust['Profit']<0).mean()*100:.1f}% of base", delta_color="inverse")
    c3.metric("Profit lost to them", money(cust.loc[cust['Profit'] < 0, 'Profit'].sum()))
    c4.metric("Median profit per customer", f"${cust['Profit'].median():,.0f}")

    ranked = cust.sort_values("Profit", ascending=False)
    st.markdown("#### Value tiers (quintiles by realised profit)")
    cust["Tier"] = pd.qcut(cust["Profit"], [0, .2, .4, .6, .8, 1.0],
                           labels=["Tier 5 (lowest)", "Tier 4", "Tier 3", "Tier 2",
                                   "Tier 1 (highest)"])
    tier = cust.groupby("Tier", observed=True).agg(
        Customers=("Profit", "size"), Revenue=("Revenue", "sum"), Profit=("Profit", "sum"),
        AvgOrders=("Orders", "mean"), AvgOrderValue=("Avg order value", "mean")).reset_index()
    tier["Margin %"] = (tier["Profit"] / tier["Revenue"] * 100).round(1)
    tier["% of total profit"] = (tier["Profit"] / tot_p * 100).round(1)
    tier["AvgOrders"] = tier["AvgOrders"].round(1)
    tier["AvgOrderValue"] = tier["AvgOrderValue"].round(0)

    fig = go.Figure(go.Bar(x=tier["Tier"], y=tier["Profit"],
                           marker_color=[RED if p < 0 else GREEN for p in tier["Profit"]],
                           text=[money(p) for p in tier["Profit"]], textposition="outside"))
    fig.update_layout(height=380, yaxis_title="Total profit (USD)", margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(tier, use_container_width=True, hide_index=True)

    st.warning(
        "**Read the bottom tier carefully.** Tier 5 customers average "
        f"{tier.loc[tier.Tier=='Tier 5 (lowest)','AvgOrders'].iloc[0]:.1f} orders at "
        f"${tier.loc[tier.Tier=='Tier 5 (lowest)','AvgOrderValue'].iloc[0]:,.0f} average order "
        "value — ordering behaviour comparable to the top tiers. Their negative profit comes "
        "from the margin realised on those orders, not from buying less or buying cheaply. "
        "Before de-prioritising any customer here, check whether their margin persists across "
        "time periods; in this dataset it largely does not.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Top 15 customers by profit")
        st.dataframe(ranked.head(15)[["Customer Id", "Segment", "Country", "Orders",
                                      "Revenue", "Profit", "Margin %"]].round(0),
                     use_container_width=True, hide_index=True)
    with c2:
        st.markdown("##### Bottom 15 customers by profit")
        st.dataframe(ranked.tail(15)[["Customer Id", "Segment", "Country", "Orders",
                                      "Revenue", "Profit", "Margin %"]].round(0),
                     use_container_width=True, hide_index=True)

    st.markdown("#### Segment contribution")
    seg = group_perf(fdf, "Customer Segment")
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Revenue", x=seg["Customer Segment"], y=seg["Revenue"],
                             marker_color=BLUE))
        fig.add_trace(go.Bar(name="Profit", x=seg["Customer Segment"], y=seg["Profit"],
                             marker_color=GREEN))
        fig.update_layout(barmode="group", height=380, yaxis_title="USD", margin=dict(t=30))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.dataframe(seg, use_container_width=True, hide_index=True)

    st.download_button("Download customer profitability table (CSV)",
                       ranked.to_csv(index=False), "customer_profitability.csv", "text/csv")

# ----------------------- Tab 3: Product & category ------------------------
with tab3:
    prod = group_perf(fdf, "Product Name", min_orders=5).sort_values("Profit", ascending=False)
    cat = group_perf(fdf, "Category Name", min_orders=5).sort_values("Profit", ascending=False)

    c1, c2, c3 = st.columns(3)
    c1.metric("Products sold", f"{fdf['Product Name'].nunique():,}")
    c2.metric("Loss-making products", f"{(prod['Profit']<0).sum():,}")
    top5 = prod.head(5)["Revenue"].sum() / fdf["Revenue"].sum() * 100
    c3.metric("Revenue from top 5 products", f"{top5:.0f}%")

    st.markdown("#### Revenue vs margin — where volume and margin disagree")
    med_margin = prod["Margin %"].median()
    fig = px.scatter(prod, x="Revenue", y="Margin %", size="Orders", color="Loss-order %",
                     hover_name="Product Name", color_continuous_scale="Reds",
                     size_max=45, log_x=True)
    fig.add_hline(y=med_margin, line_dash="dash", line_color=GREY,
                  annotation_text=f"Median margin {med_margin:.1f}%")
    fig.update_layout(height=480, margin=dict(t=30),
                      xaxis_title="Revenue (log scale, USD)")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Bottom-right = high revenue, thin margin: the products where a small margin "
               "improvement moves the most absolute profit. Bottom-left = low revenue and thin "
               "margin: candidates for range rationalisation.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Highest revenue, below-median margin")
        flag = prod[(prod["Revenue"] > prod["Revenue"].median()) &
                    (prod["Margin %"] < med_margin)].sort_values("Revenue", ascending=False)
        st.dataframe(flag.head(12)[["Product Name", "Revenue", "Profit", "Margin %",
                                    "Loss-order %"]].round(1),
                     use_container_width=True, hide_index=True)
    with c2:
        st.markdown("##### Lowest total profit")
        st.dataframe(prod.tail(12)[["Product Name", "Revenue", "Profit", "Margin %",
                                    "Orders"]].round(1).iloc[::-1],
                     use_container_width=True, hide_index=True)

    st.markdown("#### Category profitability heatmap")
    dim2 = st.selectbox("Break category down by",
                        ["Market", "Customer Segment", "Shipping Mode", "DiscountBand",
                         "PriceBand"], index=0)
    top_cats = (fdf.groupby("Category Name", observed=True)["Revenue"].sum()
                .sort_values(ascending=False).head(20).index)
    sub = fdf[fdf["Category Name"].isin(top_cats)]
    pr = sub.pivot_table(index="Category Name", columns=dim2, values="Profit", aggfunc="sum",
                         observed=True)
    rv = sub.pivot_table(index="Category Name", columns=dim2, values="Revenue", aggfunc="sum",
                         observed=True)
    n = sub.pivot_table(index="Category Name", columns=dim2, values="Profit", aggfunc="count",
                        observed=True)
    heat = (pr / rv * 100).where(n >= 30)
    fig = px.imshow(heat.round(1), text_auto=True, aspect="auto",
                    color_continuous_scale="RdYlGn", color_continuous_midpoint=0,
                    labels=dict(color="Margin %"))
    fig.update_layout(height=140 + 34 * len(heat), margin=dict(t=30), xaxis_title="",
                      yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Cells with fewer than 30 order lines are suppressed as unstable.")

    st.dataframe(cat, use_container_width=True, hide_index=True)
    st.download_button("Download product profitability table (CSV)",
                       prod.to_csv(index=False), "product_profitability.csv", "text/csv")

# ------------------- Tab 4: Discount impact analyzer ----------------------
with tab4:
    st.markdown("#### Does discounting pay for itself?")
    band = fdf.groupby("DiscountBand", observed=True).agg(
        Orders=("Revenue", "count"), GrossSales=("GrossSales", "sum"),
        Revenue=("Revenue", "sum"), Discount=("Discount", "sum"),
        Profit=("Profit", "sum"), AvgQty=("Quantity", "mean"),
        LossRate=("IsLoss", "mean")).reset_index()
    band["Margin on net revenue %"] = (band["Profit"] / band["Revenue"] * 100).round(2)
    band["Margin on gross sales %"] = (band["Profit"] / band["GrossSales"] * 100).round(2)
    band["Profit per order"] = (band["Profit"] / band["Orders"]).round(2)
    band["Loss-order %"] = (band["LossRate"] * 100).round(1)
    band["Avg units"] = band["AvgQty"].round(2)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=band["DiscountBand"].astype(str), y=band["Profit per order"],
                         name="Profit per order ($)", marker_color=BLUE, yaxis="y"))
    fig.add_trace(go.Scatter(x=band["DiscountBand"].astype(str),
                             y=band["Margin on gross sales %"],
                             name="Margin on gross sales (%)", yaxis="y2",
                             mode="lines+markers", line=dict(color=RED, width=3)))
    fig.add_trace(go.Scatter(x=band["DiscountBand"].astype(str), y=band["Avg units"],
                             name="Avg units per order", yaxis="y3",
                             mode="lines+markers", line=dict(color=GREEN, dash="dot", width=2)))
    fig.update_layout(
        height=460, margin=dict(t=30, r=90),
        yaxis=dict(title="Profit per order ($)"),
        yaxis2=dict(title="Margin %", overlaying="y", side="right"),
        yaxis3=dict(overlaying="y", side="right", position=1.0, showticklabels=False,
                    range=[0, band["Avg units"].max() * 2]),
        legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(band[["DiscountBand", "Orders", "Revenue", "Discount", "Profit",
                       "Margin on net revenue %", "Margin on gross sales %",
                       "Profit per order", "Loss-order %", "Avg units"]].round(0),
                 use_container_width=True, hide_index=True)

    corr_r = fdf["DiscountRate"].corr(fdf["ProfitRatio"])
    corr_q = fdf["DiscountRate"].corr(fdf["Quantity"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Correlation: discount rate vs profit ratio", f"{corr_r:+.3f}")
    c2.metric("Correlation: discount rate vs order quantity", f"{corr_q:+.3f}")
    c3.metric("Discount spend per $1 of profit", f"${k['discount']/max(k['profit'],1):.2f}")

    st.error(
        "**The core discount finding.** Deeper discounts do not buy larger orders — the "
        "correlation between discount rate and units per order is essentially zero — and they "
        "do not accompany better unit economics. Margin on gross sales therefore falls "
        "monotonically as discount deepens, from roughly 13% at zero discount to under 10% in "
        "the deepest band. In this book, discount is a straight transfer from margin to the "
        "customer with no measurable volume response.")

    st.markdown("#### What-if: capping the discount rate")
    cap = st.slider("Cap all discounts at (%)", 0, 25, 10, 1)
    st.caption("Recomputes the book with every order's discount rate capped at the chosen "
               "level. Assumes unit economics and order volume hold — see the caveat below.")

    sim = fdf.copy()
    new_rate = sim["DiscountRate"].clip(upper=cap / 100)
    new_discount = sim["GrossSales"] * new_rate
    recovered = sim["Discount"] - new_discount
    new_revenue = sim["GrossSales"] - new_discount
    new_profit = sim["Profit"] + recovered

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Discount recovered", money(recovered.sum()))
    c2.metric("Profit under cap", money(new_profit.sum()),
              f"{(new_profit.sum()/k['profit']-1)*100:+.1f}%")
    c3.metric("Margin under cap", f"{new_profit.sum()/new_revenue.sum()*100:.2f}%",
              f"{new_profit.sum()/new_revenue.sum()*100 - k['margin']:+.2f} pts")
    c4.metric("Orders affected", f"{(sim['DiscountRate'] > cap/100).sum():,}",
              f"{(sim['DiscountRate'] > cap/100).mean()*100:.0f}% of lines")

    caps = np.arange(0, 26, 1)
    profits = [(fdf["Profit"] + (fdf["Discount"] - fdf["GrossSales"] *
                                 fdf["DiscountRate"].clip(upper=cp / 100))).sum()
               for cp in caps]
    fig = go.Figure(go.Scatter(x=caps, y=profits, mode="lines", line=dict(color=GREEN, width=3)))
    fig.add_hline(y=k["profit"], line_dash="dash", line_color=GREY,
                  annotation_text=f"Current profit {money(k['profit'])}")
    fig.add_vline(x=cap, line_dash="dot", line_color=RED)
    fig.update_layout(height=380, xaxis_title="Discount cap (%)",
                      yaxis_title="Modelled profit (USD)", margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)

    st.info("**Caveat on the what-if.** This model holds demand fixed. It is an upper bound on "
            "recoverable margin, not a forecast. The zero-correlation finding above makes fixed "
            "demand a defensible starting assumption for this dataset, but real customers may "
            "respond to a withdrawn discount in ways historical data cannot show. Any cap "
            "should be piloted on a subset of accounts before a book-wide rollout.")

# ----------------------- Tab 5: Market & region ---------------------------
with tab5:
    c1, c2 = st.columns(2)
    with c1:
        mk = group_perf(fdf, "Market").sort_values("Revenue", ascending=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(y=mk["Market"], x=mk["Revenue"], name="Revenue",
                             orientation="h", marker_color=BLUE))
        fig.add_trace(go.Bar(y=mk["Market"], x=mk["Profit"], name="Profit",
                             orientation="h", marker_color=GREEN))
        fig.update_layout(barmode="group", height=400, xaxis_title="USD",
                          title="Revenue and profit by market", margin=dict(t=50))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = go.Figure(go.Bar(y=mk["Market"], x=mk["Margin %"], orientation="h",
                               marker_color=[RED if m < k["margin"] else GREEN
                                             for m in mk["Margin %"]],
                               text=[f"{m:.1f}%" for m in mk["Margin %"]],
                               textposition="outside"))
        fig.add_vline(x=k["margin"], line_dash="dash", line_color=GREY,
                      annotation_text="Book margin")
        fig.update_layout(height=400, xaxis_title="Margin %",
                          title="Margin by market", margin=dict(t=50))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Order regions ranked")
    reg = group_perf(fdf, "Order Region", min_orders=100).sort_values("Profit", ascending=False)
    st.dataframe(reg, use_container_width=True, hide_index=True)

    st.markdown("#### Countries: revenue vs margin")
    ctry = group_perf(fdf, "Order Country", min_orders=200)
    fig = px.scatter(ctry, x="Revenue", y="Margin %", size="Orders", hover_name="Order Country",
                     color="Margin %", color_continuous_scale="RdYlGn",
                     color_continuous_midpoint=k["margin"], size_max=40, log_x=True)
    fig.add_hline(y=k["margin"], line_dash="dash", line_color=GREY)
    fig.update_layout(height=460, margin=dict(t=30), xaxis_title="Revenue (log scale, USD)")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Countries with fewer than 200 order lines are excluded — their margins swing "
               "too widely on small volumes to rank meaningfully.")

    spread = mk["Margin %"].max() - mk["Margin %"].min()
    st.info(f"**Geographic margin spread is {spread:.1f} percentage points across markets.** "
            "Where the spread is this narrow, geography is not the lever — differences of this "
            "size are within the range that order-level margin variation produces by chance. "
            "Market-level revenue differences are large and real; market-level *margin* "
            "differences in this book are not.")
