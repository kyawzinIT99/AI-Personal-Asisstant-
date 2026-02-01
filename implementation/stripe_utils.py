import os
import stripe

stripe_api_key = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = stripe_api_key

# Hardcoded Price ID for "Premium Plan" - ideally this should be in env or config
# Using the product ID you found: prod_TqhJhf7EuIDrfQ
# We need a PRICE ID, not a Product ID, for checkout. 
# Since I only have the product ID, I will assume a default price lookup or we might need to create one.
# For now, I'll search for a price associated with the product.

PREMIUM_PRODUCT_ID = "prod_TqhJhf7EuIDrfQ" 

def get_premium_price_id():
    if not stripe.api_key:
        return None
    try:
        prices = stripe.Price.list(product=PREMIUM_PRODUCT_ID, active=True, limit=1)
        if prices.data:
            return prices.data[0].id
    except Exception as e:
        print(f"Error fetching price: {e}")
    return None

def check_subscription(email):
    """
    Checks if a user with the given email has an active subscription to the Premium Plan.
    Returns: bool
    """
    if not stripe.api_key:
        print("Stripe API key missing. Mocking subscription as False.")
        return False

    try:
        # 1. Find customer by email
        customers = stripe.Customer.list(email=email, limit=1)
        if not customers.data:
            return False
        
        customer = customers.data[0]
        
        # 2. List active subscriptions for this customer
        subscriptions = stripe.Subscription.list(customer=customer.id, status='active')
        
        # 3. Check if any subscription is for our premium product
        for sub in subscriptions.data:
            for item in sub['items'].data:
                if item.price.product == PREMIUM_PRODUCT_ID:
                    return True
                    
        return False
        
    except Exception as e:
        print(f"Stripe error checking subscription: {e}")
        return False

def create_checkout_session(email, success_url, cancel_url):
    """
    Creates a Stripe Checkout Session for the Premium Plan.
    Returns: checkout_url (str) or None
    """
    if not stripe.api_key:
        print("Stripe API key missing.")
        return None

    price_id = get_premium_price_id()
    if not price_id:
        print("No price found for premium product.")
        return None

    try:
        # Create or get customer
        customers = stripe.Customer.list(email=email, limit=1)
        if customers.data:
            customer_id = customers.data[0].id
        else:
            customer = stripe.Customer.create(email=email)
            customer_id = customer.id

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session.url
    except Exception as e:
        print(f"Stripe error creating session: {e}")
        return None
