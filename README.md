# Marketplace Profitability and Returns
[Open the interactive dashboard](https://marketplace-profitability-a.streamlit.app)

A seller profitability analysis project built with Python, Pandas,
DuckDB SQL, Streamlit, and Plotly.

## Business problem

High sales do not always translate into strong contribution profit.

This project investigates how discounts, refunds, product costs,
marketplace fees, and delivery expenses affect product and seller
profitability.

## Dashboard

![Business overview](screenshots/overview.png)

![Returns analysis](screenshots/returns.png)

![Product profitability](screenshots/profitability.png)

## Workflow

1. Generate reproducible synthetic source data with Python.
2. Validate identifiers, return quantities, refunds, and dates.
3. Aggregate return events in SQL before joining to orders.
4. Calculate order-level contribution economics.
5. Explore results through an interactive Streamlit report.

## Dataset

- 4,000 synthetic orders across 2025.
- Eight products across four categories.
- Four fictional sellers.
- One product line per order.
- Full and partial quantity returns.
- Some orders have multiple return events.
- All currency values are INR.

Data is generated using a fixed random seed.

## Metrics

- Net revenue = paid sales - refunds.
- Net product cost = original product cost - recovered inventory cost.
- Contribution profit = net revenue - net product cost -
  marketplace fees - outbound shipping - return shipping.
- Contribution margin = total contribution profit / total net revenue.
- Unit return rate = returned units / units sold.

## Assumptions

- Analysis uses the seller perspective.
- Marketplace fees reverse proportionally with refunds.
- Restockable returns recover original inventory cost.
- Taxes, fixed overhead, and subsequent inventory resale are excluded.
- Date filters select order cohorts and include all recorded returns
  associated with those orders.
- Synthetic patterns demonstrate analytical methods and are not
  evidence about an actual marketplace.

## Validation

- Unique source identifiers.
- Valid product, seller, and order references.
- Returned quantities do not exceed purchased quantities.
- Refunds do not exceed paid amounts.
- Return dates follow order dates.
- SQL preserves one row per order.
- Source sales and refunds reconcile with analytical totals.
- Contribution profit reconciles with its components.

## Run locally

Use the Python version recorded in the repository's setup notes.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python generate_data.py
python -m streamlit run app.py
```

## Project files

- `generate_data.py` generates and validates source data.
- `sql/profitability.sql` calculates order profitability.
- `app.py` provides the interactive dashboard.
- `data/` contains reproducible synthetic source files.
- `screenshots/` contains report previews.
- `requirements.txt` records Python dependencies.

## Findings

These observations describe the synthetic demonstration dataset.
All categories and sellers were selected for orders placed between
1 January and 31 December 2025. Recorded returns associated with
those orders are included, even when returned later.

### 1. Overall profitability and returns

The dataset generated net revenue of ₹9,537,540 and contribution
profit of ₹2,464,177, producing a contribution margin of 25.8%.
The overall unit return rate was 12.0%.

A follow-up analysis would compare category return rates and
investigate how refunds, inventory recovery, and return shipping
affect contribution profit.

### 2. Product with the lowest contribution profit

Storage Organizer recorded the lowest total contribution profit
among the eight products, at approximately ₹225,000 based on
the chart.

Its contribution margin was higher than several products with
greater total contribution profit. A follow-up analysis would
compare units sold, revenue, discounts, and return-related costs
to understand the difference.

### 3. Return reason with the highest refund amount

Damaged products accounted for the highest total refund amount,
at approximately ₹310,000 based on the chart.

A follow-up analysis would identify the products and sellers
associated with these returns and examine packaging, shipping,
and product-quality factors. The chart establishes the refund
ranking, while the underlying causes require further investigation.