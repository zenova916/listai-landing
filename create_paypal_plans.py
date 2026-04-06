"""
create_paypal_plans.py
Run this ONCE on your computer to create the 3 PayPal subscription plans.
It will print the Plan IDs — copy them into Render env vars.

Usage:
  1. Fill in your PayPal LIVE credentials below
  2. Run: python create_paypal_plans.py
  3. Copy the 3 Plan IDs printed at the end
"""

import httpx
import base64
import json

# ── FILL THESE IN ─────────────────────────────────────────────
PAYPAL_CLIENT_ID     = "AWTp41mGgaukfm1lKTX6lIWOO-Qqgb2n_Mn0K0Hww7tcyCDQofMkANR7Z3EiAIFuVL1fIFlPz9tkgoak"
PAYPAL_CLIENT_SECRET = "EMqx_2Pv-GGG97_9WfHRnQVKgqdDz1dwCi1sBTBBGWHDePHxJOyI6G7bsKr6Bw4mE9NhG2z5p77qcWo9"
PRODUCT_ID           = ""  # the one you already created
MODE                 = "live"  # change to "sandbox" to test first
# ──────────────────────────────────────────────────────────────

BASE = "https://api.paypal.com" if MODE == "live" else "https://api.sandbox.paypal.com"


def get_token():
    creds = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()).decode()
    r = httpx.post(
        f"{BASE}/v1/oauth2/token",
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
        timeout=15,
    )
    data = r.json()
    if "access_token" not in data:
        print("❌ Failed to get PayPal token. Check your Client ID and Secret.")
        print(json.dumps(data, indent=2))
        exit(1)
    print("✅ PayPal authenticated")
    return data["access_token"]


def create_plan(token, name, description, price_usd):
    r = httpx.post(
        f"{BASE}/v1/billing/plans",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "product_id": PRODUCT_ID,
            "name": name,
            "description": description,
            "status": "ACTIVE",
            "billing_cycles": [
                {
                    "frequency": {
                        "interval_unit": "MONTH",
                        "interval_count": 1,
                    },
                    "tenure_type": "REGULAR",
                    "sequence": 1,
                    "total_cycles": 0,  # 0 = infinite (recurring monthly)
                    "pricing_scheme": {
                        "fixed_price": {
                            "value": str(price_usd),
                            "currency_code": "USD",
                        }
                    },
                }
            ],
            "payment_preferences": {
                "auto_bill_outstanding": True,
                "setup_fee": {"value": "0", "currency_code": "USD"},
                "setup_fee_failure_action": "CONTINUE",
                "payment_failure_threshold": 3,
            },
        },
        timeout=15,
    )
    data = r.json()
    if "id" not in data:
        print(f"❌ Failed to create plan: {name}")
        print(json.dumps(data, indent=2))
        return None
    return data["id"]


def main():
    print(f"\n{'='*50}")
    print(f"  Creating EbayListAI PayPal Plans ({MODE.upper()})")
    print(f"{'='*50}\n")

    token = get_token()

    plans = [
        {
            "name": "EbayListAI Starter",
            "description": "50 listings per month, 1 eBay account",
            "price": 29,
            "env_key": "PAYPAL_PLAN_STARTER",
        },
        {
            "name": "EbayListAI Pro",
            "description": "500 listings per month, 3 eBay accounts, image upload",
            "price": 79,
            "env_key": "PAYPAL_PLAN_PRO",
        },
        {
            "name": "EbayListAI Agency",
            "description": "Unlimited listings, 10 eBay accounts, team seats",
            "price": 199,
            "env_key": "PAYPAL_PLAN_AGENCY",
        },
    ]

    results = []
    for plan in plans:
        print(f"Creating {plan['name']} (${plan['price']}/month)...")
        plan_id = create_plan(token, plan["name"], plan["description"], plan["price"])
        if plan_id:
            print(f"  ✅ Created: {plan_id}")
            results.append((plan["env_key"], plan_id))
        else:
            print(f"  ❌ Failed — check error above")

    print(f"\n{'='*50}")
    print("  ADD THESE TO RENDER ENVIRONMENT VARIABLES:")
    print(f"{'='*50}\n")
    for key, val in results:
        print(f"  {key} = {val}")
    print(f"\n{'='*50}")
    print("  Also add these if not already set:")
    print(f"{'='*50}")
    print(f"  PAYPAL_MODE              = {MODE}")
    print(f"  PAYPAL_CLIENT_ID         = {PAYPAL_CLIENT_ID[:8]}...")
    print(f"  PAYPAL_CLIENT_SECRET     = (your secret)")
    print(f"\n✅ Done! Copy the Plan IDs above into Render.\n")


if __name__ == "__main__":
    main()
