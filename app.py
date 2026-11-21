from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

st.set_page_config(
    page_title="Marketplace Profitability",
    page_icon="📊",
    layout="wide",
)


@st.cache_data
def load_data():
    tables = {
        name: pd.read_csv(DATA / f"{name}.csv")
        for name in ["orders", "returns", "products", "sellers"]
    }

    tables["orders"]["order_date"] = pd.to_datetime(
        tables["orders"]["order_date"]
    )
    tables["returns"]["return_date"] = pd.to_datetime(
        tables["returns"]["return_date"]
    )

    sql = (ROOT / "sql" / "profitability.sql").read_text()

    with duckdb.connect(":memory:") as connection:
        for name, frame in tables.items():
            connection.register(name, frame)

        profitability = connection.execute(sql).fetchdf()

    # SQL must preserve exactly one row per order.
    assert profitability["order_id"].is_unique
    assert len(profitability) == len(tables["orders"])

    assert abs(
        profitability["paid_amount"].sum()
        - tables["orders"]["paid_amount"].sum()
    ) < 0.01

    assert abs(
        profitability["refund_amount"].sum()
        - tables["returns"]["refund_amount"].sum()
    ) < 0.01

    expected_profit = (
        profitability["net_revenue"]
        - profitability["net_product_cost"]
        - profitability["marketplace_fee"]
        - profitability["shipping_cost"]
        - profitability["return_shipping_cost"]
    )

    assert (
        expected_profit - profitability["contribution_profit"]
    ).abs().max() < 0.01

    return profitability, tables["returns"]


def money(value):
    return f"₹{value:,.0f}"


def summarize(frame, group):
    result = frame.groupby(group, as_index=False).agg(
        orders=("order_id", "nunique"),
        net_revenue=("net_revenue", "sum"),
        contribution_profit=("contribution_profit", "sum"),
        refund_amount=("refund_amount", "sum"),
        units_sold=("quantity", "sum"),
        units_returned=("returned_quantity", "sum"),
    )

    result["margin_pct"] = (
        result["contribution_profit"]
        .div(result["net_revenue"].replace(0, float("nan")))
        .mul(100)
    )

    result["unit_return_rate_pct"] = (
        result["units_returned"].div(result["units_sold"]).mul(100)
    )

    return result


st.title("Marketplace Profitability and Returns")
st.caption(
    "Synthetic portfolio dataset • Seller contribution economics • INR"
)

required_files = [
    DATA / f"{name}.csv"
    for name in ["orders", "returns", "products", "sellers"]
]

if not all(path.exists() for path in required_files):
    st.error("Sample data is missing. Run: python generate_data.py")
    st.stop()

orders, return_events = load_data()

st.sidebar.header("Filters")

date_range = st.sidebar.date_input(
    "Order date range",
    value=(
        orders["order_date"].min().date(),
        orders["order_date"].max().date(),
    ),
    min_value=orders["order_date"].min().date(),
    max_value=orders["order_date"].max().date(),
)

categories = st.sidebar.multiselect(
    "Categories",
    options=sorted(orders["category"].unique()),
    default=sorted(orders["category"].unique()),
)

sellers = st.sidebar.multiselect(
    "Sellers",
    options=sorted(orders["seller_name"].unique()),
    default=sorted(orders["seller_name"].unique()),
)

page = st.sidebar.radio(
    "Report page",
    [
        "Business overview",
        "Returns analysis",
        "Product and seller profitability",
    ],
)

if len(date_range) != 2:
    st.info("Choose both a start date and an end date.")
    st.stop()

start_date, end_date = date_range

filtered = orders.loc[
    orders["order_date"].dt.date.between(start_date, end_date)
    & orders["category"].isin(categories)
    & orders["seller_name"].isin(sellers)
].copy()

if filtered.empty:
    st.info("No orders match these filters. Expand your selection.")
    st.stop()

revenue = filtered["net_revenue"].sum()
profit = filtered["contribution_profit"].sum()
margin = profit / revenue * 100 if revenue else None
unit_return_rate = (
    filtered["returned_quantity"].sum()
    / filtered["quantity"].sum()
    * 100
)

columns = st.columns(4)
columns[0].metric("Net revenue", money(revenue))
columns[1].metric("Contribution profit", money(profit))
columns[2].metric(
    "Contribution margin",
    f"{margin:.1f}%" if margin is not None else "N/A",
)
columns[3].metric("Unit return rate", f"{unit_return_rate:.1f}%")

st.caption(
    "Dates filter order cohorts. All recorded returns for those orders "
    "are included, even when the return occurred later."
)

if page == "Business overview":
    st.subheader("Monthly performance")

    filtered["month"] = (
        filtered["order_date"].dt.to_period("M").dt.to_timestamp()
    )

    monthly = summarize(filtered, "month")

    figure = px.line(
        monthly,
        x="month",
        y=["net_revenue", "contribution_profit"],
        markers=True,
        labels={"value": "Amount (INR)", "month": "Order month"},
    )
    st.plotly_chart(figure, use_container_width=True)

    st.subheader("Where paid sales become contribution profit")

    bridge = pd.DataFrame(
        {
            "Component": [
                "Paid sales",
                "Refunds",
                "Net product cost",
                "Marketplace fees",
                "Outbound shipping",
                "Return shipping",
                "Contribution profit",
            ],
            "Amount (INR)": [
                filtered["paid_amount"].sum(),
                -filtered["refund_amount"].sum(),
                -filtered["net_product_cost"].sum(),
                -filtered["marketplace_fee"].sum(),
                -filtered["shipping_cost"].sum(),
                -filtered["return_shipping_cost"].sum(),
                profit,
            ],
        }
    )
    st.dataframe(bridge, hide_index=True, use_container_width=True)

    st.subheader("Category performance")
    st.dataframe(
        summarize(filtered, "category").round(2),
        hide_index=True,
        use_container_width=True,
    )

elif page == "Returns analysis":
    st.subheader("Returns by reason")

    selected_returns = return_events.loc[
        return_events["order_id"].isin(filtered["order_id"])
    ]

    if selected_returns.empty:
        st.info("These orders have no recorded returns.")
    else:
        reasons = selected_returns.groupby(
            "reason", as_index=False
        ).agg(
            returned_units=("returned_quantity", "sum"),
            refund_amount=("refund_amount", "sum"),
        )

        figure = px.bar(
            reasons,
            x="reason",
            y="refund_amount",
            color="returned_units",
            labels={
                "reason": "Return reason",
                "refund_amount": "Refund amount (INR)",
            },
        )
        st.plotly_chart(figure, use_container_width=True)

        st.dataframe(
            reasons.round(2),
            hide_index=True,
            use_container_width=True,
        )

    st.subheader("Category return rates")
    category_returns = summarize(filtered, "category")

    figure = px.bar(
        category_returns,
        x="category",
        y="unit_return_rate_pct",
        labels={
            "category": "Category",
            "unit_return_rate_pct": "Returned units (%)",
        },
    )
    st.plotly_chart(figure, use_container_width=True)

else:
    st.subheader("Product profitability")

    products = summarize(filtered, "product_name")
    products = products.sort_values("contribution_profit")

    figure = px.bar(
        products,
        x="contribution_profit",
        y="product_name",
        orientation="h",
        color="margin_pct",
        color_continuous_scale="RdYlGn",
        labels={
            "contribution_profit": "Contribution profit (INR)",
            "product_name": "Product",
            "margin_pct": "Margin (%)",
        },
    )
    st.plotly_chart(figure, use_container_width=True)

    st.dataframe(
        products.round(2),
        hide_index=True,
        use_container_width=True,
    )

    st.subheader("Seller profitability")
    st.dataframe(
        summarize(filtered, "seller_name").round(2),
        hide_index=True,
        use_container_width=True,
    )

    loss_orders = filtered.loc[
        filtered["contribution_profit"] < 0
    ]

    st.metric("Orders with negative contribution", len(loss_orders))

with st.expander("Definitions and assumptions"):
    st.markdown(
        """
- Net revenue = paid sales minus refunds.
- Net product cost = original product cost minus recovered inventory cost.
- Contribution profit = net revenue minus net product cost,
  marketplace fees, outbound shipping, and return shipping.
- Contribution margin = total contribution profit / total net revenue.
- Unit return rate = returned units / units sold.
- Fees are assumed to reverse proportionally with refunds.
- Restockable returns recover original inventory cost.
- Taxes, fixed overhead, and later resale of returned inventory are excluded.
- One product line per order. Multiple return events are supported.
- Patterns reflect synthetic data generation assumptions.
        """
    )

with st.expander("Order-level calculations"):
    st.dataframe(
        filtered,
        hide_index=True,
        use_container_width=True,
    )

st.download_button(
    "Download filtered order analysis",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="marketplace_analysis.csv",
    mime="text/csv",
)