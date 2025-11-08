# Product Catalog Schema Documentation

This document describes the schema for the `product_offers` table and the product catalog JSON format.

## Database Schema

### Table: `product_offers`

The `product_offers` table stores financial products (savings accounts, credit cards, apps, services, investment accounts) that can be recommended to users based on their persona and financial signals.

#### Core Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `product_id` | TEXT | PRIMARY KEY | Unique identifier (e.g., "prod_001") |
| `product_name` | TEXT | NOT NULL | Product name (e.g., "Chase Slate Edge") |
| `product_type` | TEXT | NOT NULL, CHECK | One of: `savings_account`, `credit_card`, `app`, `service`, `investment_account` |
| `category` | TEXT | NOT NULL | Product category (e.g., `balance_transfer`, `hysa`, `budgeting_app`, `subscription_manager`, `robo_advisor`) |
| `persona_targets` | TEXT | NOT NULL | JSON array of target personas: `["high_utilization", "variable_income", "subscription_heavy", "savings_builder", "wealth_builder"]` |

#### Eligibility Criteria

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `min_income` | REAL | 0.0 | Minimum monthly income required (in dollars) |
| `max_credit_utilization` | REAL | 1.0 | Maximum credit utilization allowed (0.0-1.0, 1.0 = no restriction) |
| `requires_no_existing_savings` | BOOLEAN | FALSE | If true, product only for users without savings accounts |
| `requires_no_existing_investment` | BOOLEAN | FALSE | If true, product only for users without investment accounts |
| `min_credit_score` | INTEGER | NULL | Minimum credit score required (NULL if not applicable) |

#### Content Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `short_description` | TEXT | NOT NULL | One-sentence product description (under 100 chars) |
| `benefits` | TEXT | NOT NULL | JSON array of benefit strings (3-5 benefits) |
| `typical_apy_or_fee` | TEXT | NULL | APY or fee information (e.g., "4.5% APY", "0% intro APR for 18mo", "$10/month") |
| `partner_link` | TEXT | NULL | Partner referral link (placeholder URL for MVP) |
| `disclosure` | TEXT | NOT NULL | Standard disclaimer text |

#### Business Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `partner_name` | TEXT | NOT NULL | Partner/institution name (extracted from product name) |
| `commission_rate` | REAL | 0.0 | Commission rate (placeholder for MVP) |
| `priority` | INTEGER | 1 | Display priority (1 = high, 2+ = lower) |
| `active` | BOOLEAN | TRUE | Whether product is currently active |

#### Timestamps

| Field | Type | Description |
|-------|------|-------------|
| `created_at` | DATETIME | Auto-set on creation |
| `updated_at` | DATETIME | Auto-updated on modification |

#### Indexes

- `idx_product_offers_persona_targets` on `persona_targets` - For filtering by persona
- `idx_product_offers_active` on `active` - For filtering active products

## JSON Catalog Format

The product catalog JSON file (`data/product_catalog.json`) contains an array of product objects:

```json
{
  "products": [
    {
      "product_id": "prod_001",
      "product_name": "Chase Slate Edge",
      "product_type": "credit_card",
      "category": "balance_transfer",
      "persona_targets": ["high_utilization"],
      "short_description": "Balance transfer card with 0% intro APR",
      "benefits": [
        "0% intro APR for 18 months on balance transfers",
        "No annual fee",
        "Free credit score monitoring"
      ],
      "typical_apy_or_fee": "0% intro APR for 18mo, then 20.49% variable",
      "min_income": 2000,
      "max_credit_utilization": 0.85,
      "requires_no_existing_savings": false,
      "requires_no_existing_investment": false,
      "min_credit_score": 670,
      "partner_name": "Chase",
      "partner_link": "https://example.com/prod_001",
      "commission_rate": 0.0,
      "priority": 1,
      "active": true,
      "disclosure": "This is educational content, not financial advice. Product terms, rates, and availability subject to change. SpendSense may receive compensation from partners. Consult a licensed financial advisor for personalized guidance.",
      "created_at": "2025-01-07T00:00:00Z",
      "updated_at": "2025-01-07T00:00:00Z"
    }
  ]
}
```

## Eligibility Criteria Guidelines

### Balance Transfer Cards
- `min_income`: $2000-3000/month
- `max_credit_utilization`: 0.75-0.85 (typically <0.85)
- `min_credit_score`: 670+
- `requires_no_existing_savings`: false
- `requires_no_existing_investment`: false

### High-Yield Savings Accounts (HYSA)
- `min_income`: 0 (no restriction)
- `max_credit_utilization`: 1.0 (no restriction)
- `min_credit_score`: null
- `requires_no_existing_savings`: typically false (users can have multiple)
- `requires_no_existing_investment`: false

### Investment Accounts / Robo-Advisors
- `min_income`: $5000-10000/month
- `max_credit_utilization`: 1.0 (no restriction, but typically low utilization users)
- `min_credit_score`: null
- `requires_no_existing_savings`: false
- `requires_no_existing_investment`: typically false (but may be true for some products)

### Budgeting Apps
- `min_income`: 0 (no restriction)
- `max_credit_utilization`: 1.0 (no restriction)
- `min_credit_score`: null
- `requires_no_existing_savings`: false
- `requires_no_existing_investment`: false

### Subscription Managers
- `min_income`: 0 (no restriction)
- `max_credit_utilization`: 1.0 (no restriction)
- `min_credit_score`: null
- `requires_no_existing_savings`: false
- `requires_no_existing_investment`: false

## Persona Targeting

Each product targets one or more personas:

- **high_utilization**: Users with high credit card debt (>50% utilization, interest charges)
- **variable_income**: Freelancers/gig workers with irregular income (pay gaps >45 days, low buffer)
- **subscription_heavy**: Users spending heavily on subscriptions (5+ recurring merchants, >20% of spending)
- **savings_builder**: Users actively building emergency funds (positive savings growth, <3 months emergency fund)
- **wealth_builder**: Affluent users ready for investing/retirement (>$5k monthly income, low debt, emergency fund established)

Products should target 4-5 products per persona minimum, with some overlap allowed.

## Standard Disclosure

All products must include the following disclosure text:

> "This is educational content, not financial advice. Product terms, rates, and availability subject to change. SpendSense may receive compensation from partners. Consult a licensed financial advisor for personalized guidance."

## Related Documentation

- See `scripts/generate_product_catalog.py` for catalog generation
- See `scripts/test_ingest_products.py` for product ingestion via API (PR #39)
- See `backend/app/services/product_matcher.py` for product matching logic (PR #40)
- See `backend/app/services/guardrails.py` for eligibility checking (PR #41)

