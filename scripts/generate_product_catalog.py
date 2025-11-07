# scripts/generate_product_catalog.py

import json
from openai import OpenAI

client = OpenAI()

PROMPT = """
Generate a realistic product catalog for a financial education platform. 
For each persona, create 4-5 relevant financial products that would help them improve their financial situation.

Personas:
1. high_utilization - Users with high credit card debt (>50% utilization, interest charges)
2. variable_income - Freelancers/gig workers with irregular income (pay gaps >45 days, low buffer)
3. subscription_heavy - Users spending heavily on subscriptions (5+ recurring merchants, >20% of spending)
4. savings_builder - Users actively building emergency funds (positive savings growth, <3 months emergency fund)
5. wealth_builder - Affluent users ready for investing/retirement (>$5k monthly income, low debt, emergency fund established)

For EACH product, provide:
- product_name: Real-sounding product name (e.g., "Chase Slate Edge", "Marcus High-Yield Savings")
- product_type: savings_account, credit_card, app, service, investment_account
- category: balance_transfer, hysa, budgeting_app, subscription_manager, robo_advisor, personal_loan, debt_consolidation, etc.
- persona_targets: Array of persona slugs this product helps (can be multiple) - use exact slugs: "high_utilization", "variable_income", "subscription_heavy", "savings_builder", "wealth_builder"
- short_description: One sentence (under 100 chars)
- benefits: Array of 3-5 specific, quantifiable benefits
- typical_apy_or_fee: If applicable (e.g., "4.5% APY", "0% intro APR for 18mo", "$10/month", "0.25% advisory fee")
- min_income: Minimum monthly income required in dollars (0 if none). Examples: 2000 for balance transfer cards, 5000+ for investment accounts
- max_credit_utilization: Maximum utilization allowed as decimal 0.0-1.0 (1.0 if no restriction). Balance transfer cards typically require <0.85
- requires_no_existing_savings: Boolean (true if product targets users without savings accounts)
- requires_no_existing_investment: Boolean (true if product targets users without investment accounts)
- min_credit_score: Minimum credit score if applicable (e.g., 670 for balance transfer cards, null if not applicable)
- disclosure: Standard disclaimer text - use this template: "This is educational content, not financial advice. Product terms, rates, and availability subject to change. SpendSense may receive compensation from partners. Consult a licensed financial advisor for personalized guidance."

Return as JSON with structure: {"products": [array of 20-25 products]}

Ensure good coverage across all 5 personas (4-5 products per persona minimum, some overlap is fine).

Use real product names where possible (Chase, Marcus, Ally, Wealthfront, YNAB, Rocket Money, etc.) but it's okay to create realistic-sounding names if needed.

Make eligibility criteria realistic:
- Balance transfer cards: min_income 2000-3000, max_credit_utilization 0.75-0.85, min_credit_score 670+
- HYSA accounts: typically no restrictions (min_income 0, max_credit_utilization 1.0)
- Investment accounts: min_income 5000-10000, typically requires low debt
- Budgeting apps: typically no restrictions
- Subscription managers: typically no restrictions
"""

def generate_product_catalog():
    """Generate product catalog using OpenAI GPT-4o"""
    print("Calling OpenAI API...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Use 4o for better quality on this one-time task
            messages=[
                {"role": "system", "content": "You are a financial product expert helping create a realistic product catalog."},
                {"role": "user", "content": PROMPT}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        products_json = response.choices[0].message.content
        products = json.loads(products_json)
        
        if "products" not in products:
            raise ValueError("Response missing 'products' key")
        
        return products["products"]
    except Exception as e:
        print(f"Error generating product catalog: {e}")
        raise


def validate_product(product, index):
    """Validate that product has all required fields"""
    required_fields = [
        "product_name", "product_type", "category", "persona_targets",
        "short_description", "benefits", "disclosure"
    ]
    missing = [f for f in required_fields if f not in product or not product[f]]
    
    if missing:
        print(f"⚠️  Product {index + 1} missing fields: {missing}")
        return False
    
    # Validate persona targets
    valid_personas = {"high_utilization", "variable_income", "subscription_heavy", "savings_builder", "wealth_builder"}
    if not isinstance(product.get("persona_targets"), list):
        print(f"⚠️  Product {index + 1} has invalid persona_targets (not a list)")
        return False
    
    invalid_personas = [p for p in product["persona_targets"] if p not in valid_personas]
    if invalid_personas:
        print(f"⚠️  Product {index + 1} has invalid personas: {invalid_personas}")
        return False
    
    return True


def enhance_products(products):
    """Add additional fields needed for our database"""
    valid_products = []
    
    for i, product in enumerate(products):
        # Validate first
        if not validate_product(product, i):
            print(f"   Skipping product {i + 1}: {product.get('product_name', 'Unknown')}")
            continue
        
        # Add metadata fields
        product["product_id"] = f"prod_{i+1:03d}"
        product["partner_name"] = extract_partner_name(product["product_name"])
        product["partner_link"] = f"https://example.com/{product['product_id']}"  # Placeholder
        product["commission_rate"] = 0.0  # Placeholder
        product["priority"] = 1 if i < 5 else 2  # First 5 are high priority
        product["active"] = True
        product["created_at"] = "2025-11-07T00:00:00Z"
        product["updated_at"] = "2025-11-07T00:00:00Z"
        
        # Ensure numeric fields have defaults
        product.setdefault("min_income", 0)
        product.setdefault("max_credit_utilization", 1.0)
        product.setdefault("requires_no_existing_savings", False)
        product.setdefault("requires_no_existing_investment", False)
        product.setdefault("min_credit_score", None)
        
        valid_products.append(product)
    
    return valid_products


def extract_partner_name(product_name):
    """Extract partner name from product name"""
    # Simple extraction: first word or two
    words = product_name.split()
    if len(words) >= 2 and words[1] not in ["High-Yield", "Checking", "Savings"]:
        return f"{words[0]} {words[1]}"
    return words[0]


def save_to_json(products, filename="data/product_catalog.json"):
    with open(filename, 'w') as f:
        json.dump(products, f, indent=2)
    print(f"Saved {len(products)} products to {filename}")


if __name__ == "__main__":
    print("=" * 60)
    print("SpendSense Product Catalog Generator")
    print("=" * 60)
    
    print("\n📝 Generating product catalog using GPT-4o...")
    products = generate_product_catalog()
    
    print(f"✓ Generated {len(products)} raw products")
    
    print("\n🔧 Validating and enhancing with additional fields...")
    products = enhance_products(products)
    
    print(f"✓ {len(products)} valid products after validation")
    
    if len(products) < 20:
        print(f"⚠️  Warning: Only {len(products)} products generated (target: 20-25)")
        print("   Consider re-running the script")
    
    print("\n💾 Saving to JSON...")
    save_to_json(products)
    
    print("\n" + "=" * 60)
    print("Sample product:")
    print("=" * 60)
    print(json.dumps(products[0], indent=2))
    
    print("\n" + "=" * 60)
    print("Distribution by persona:")
    print("=" * 60)
    from collections import Counter
    persona_counts = Counter()
    category_counts = Counter()
    
    for product in products:
        for persona in product["persona_targets"]:
            persona_counts[persona] += 1
        category_counts[product["category"]] += 1
    
    for persona, count in sorted(persona_counts.items()):
        print(f"  {persona}: {count} products")
    
    print("\n" + "=" * 60)
    print("Distribution by category:")
    print("=" * 60)
    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count} products")
    
    print("\n" + "=" * 60)
    print("✅ Product catalog generation complete!")
    print(f"📁 Output file: data/product_catalog.json")
    print("=" * 60)