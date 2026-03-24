# Shopify Commerce Setup Reference

CrabEgg connects content to commerce. This reference covers storefront setup,
product listing, checkout flow, and sales attribution.

---

## Two Paths

### Path A: User Has Existing Shopify Store
1. Collect store URL and API access token
2. Verify connection: `GET /admin/api/2024-01/shop.json`
3. List products: `GET /admin/api/2024-01/products.json`
4. Match product by name or let user select
5. Get variant IDs for checkout link generation
6. Generate trackable checkout URLs

### Path B: User Needs New Store
Guide through setup:
1. Sign up at https://www.shopify.com/free-trial
2. Add product (name, description, price, images)
3. Install a custom app for API access:
   - Shopify Admin → Settings → Apps → Develop apps
   - Create app → Configure scopes (read_products, write_products, read_orders)
   - Install app → Copy Admin API access token
4. Provide the access token to CrabEgg

---

## Product Description Generation

When setting up a new product, CrabEgg generates the listing copy:

```
Write a Shopify product description for:
Product: {{product_name}}
Pitch: {{product_pitch}}
Price: {{price}}
Audience: {{target_audience}}
Voice: {{brand_voice}}

Generate:
1. Title (max 70 chars, SEO-optimized)
2. Description (HTML, 150-300 words, benefit-focused)
3. Meta title (max 60 chars)
4. Meta description (max 155 chars)
5. Tags (comma-separated, for internal organization)
```

---

## Trackable Checkout Links

For each piece of content, generate a unique checkout URL:

### Using Storefront API (preferred)
```graphql
mutation {
  checkoutCreate(input: {
    lineItems: [{ variantId: "gid://shopify/ProductVariant/xxx", quantity: 1 }]
    customAttributes: [
      { key: "content_id", value: "vid_001" }
      { key: "source", value: "tiktok" }
      { key: "builder_id", value: "builder_xxx" }
    ]
  }) {
    checkout {
      webUrl
    }
  }
}
```

### Using Discount Codes
Alternative: Create unique discount codes per video:
```
POST /admin/api/2024-01/price_rules.json
{
  "price_rule": {
    "title": "VID001-20OFF",
    "target_type": "line_item",
    "target_selection": "all",
    "allocation_method": "across",
    "value_type": "percentage",
    "value": "-20.0",
    "usage_limit": 100,
    "starts_at": "2026-01-01T00:00:00Z"
  }
}
```

Then create the discount code:
```
POST /admin/api/2024-01/price_rules/{rule_id}/discount_codes.json
{
  "discount_code": { "code": "VID001-20OFF" }
}
```

---

## Sales Attribution

### Webhook Setup
Register for order webhooks:
```
POST /admin/api/2024-01/webhooks.json
{
  "webhook": {
    "topic": "orders/create",
    "address": "https://your-server.com/webhooks/orders",
    "format": "json"
  }
}
```

### Attribution Logic
When an order comes in:
1. Check `custom_attributes` for `content_id` and `builder_id`
2. Check `discount_codes` for video-specific codes
3. Check `landing_page` for UTM parameters
4. Match to content-pipeline entry
5. Log attribution in `data/performance-log.json`

### Performance Log Entry
```json
{
  "order_id": "shopify_order_123",
  "content_id": "vid_001",
  "builder_id": "builder_xxx",
  "revenue": 29.99,
  "commission": 7.50,
  "commission_rate": 0.25,
  "attribution_method": "discount_code",
  "order_date": "ISO-8601",
  "product_name": "...",
  "source_platform": "tiktok"
}
```

---

## Commission Tracking

If the brand has builders/affiliates selling for them:

### Commission Calculation
```python
def calculate_commission(order_total, commission_rate, payment_method):
    commission = order_total * commission_rate

    if payment_method == "stripe":
        # Stripe takes ~2.9% + $0.30
        stripe_fee = (order_total * 0.029) + 0.30
        net_commission = commission  # commission on gross, fees on brand
    elif payment_method == "crypto":
        # USDC transfer, minimal fees
        net_commission = commission

    return {
        "gross_commission": commission,
        "net_commission": net_commission,
        "payment_method": payment_method
    }
```

### Payout Schedule
- Track cumulative earnings per builder
- Payout threshold: $50 minimum
- Payout frequency: weekly or monthly (brand configures)
- Generate payout reports in `logs/sales-log.json`
