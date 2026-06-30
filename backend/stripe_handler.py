"""
Stripe integration — Checkout Session creation, webhook handling, idempotency.

Key security properties:
  1. Idempotency: payments.stripe_checkout_session_id has a UNIQUE constraint,
     so duplicate webhook events cannot create duplicate payment records.
  2. Signature verification: construct_event() cryptographically verifies
     that the webhook came from Stripe (not a forged request).
  3. Fulfillment check: payment_status is checked before granting PRO access.
"""
import logging
import os
from datetime import datetime, timezone
from typing import Optional

import stripe

from db import get_db

logger = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────────────────────

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
PRO_PRICE_ID = os.environ.get("STRIPE_PRO_PRICE_ID", "")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")


# ─── Checkout Session ─────────────────────────────────────────────────────────


def create_checkout_session(
    user_id: int,
    user_email: str,
    success_url: str = "http://localhost:5173?payment=success",
    cancel_url: str = "http://localhost:5173?payment=cancel",
) -> dict:
    """Create a Stripe Checkout Session for the PRO monthly subscription.

    Args:
        user_id: Our internal user ID (passed as client_reference_id).
        user_email: User's email for pre-filling the Stripe checkout form.
        success_url: Redirect URL after successful payment.
        cancel_url: Redirect URL if the user cancels.

    Returns:
        {"session_id": "cs_...", "url": "https://checkout.stripe.com/..."}
    """
    if not stripe.api_key:
        raise ValueError("STRIPE_SECRET_KEY is not configured.")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[
                {
                    "price": PRO_PRICE_ID,
                    "quantity": 1,
                }
            ],
            customer_email=user_email,
            client_reference_id=str(user_id),
            success_url=success_url + "&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata={
                "user_id": str(user_id),
            },
        )

        # Record a pending payment entry (idempotency key = session ID)
        db = get_db()
        try:
            db.execute(
                """INSERT INTO payments
                   (user_id, stripe_checkout_session_id, amount, currency, status)
                   VALUES (?, ?, ?, 'usd', 'pending')""",
                (user_id, session.id, 499),  # $4.99 in cents
            )
            db.commit()
        except Exception:
            # If insert fails (e.g., UNIQUE constraint), the session already
            # exists — that's fine, it means a previous attempt for this user.
            pass

        return {
            "session_id": session.id,
            "url": session.url,
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe Checkout Session creation failed: {e}")
        raise


# ─── Webhook Handler ───────────────────────────────────────────────────────────


def handle_webhook(payload: bytes, sig_header: str) -> dict:
    """Verify and process a Stripe webhook event.

    Args:
        payload: Raw request body bytes.
        sig_header: Value of the Stripe-Signature header.

    Returns:
        {"received": True, "type": "checkout.session.completed", ...}

    Raises:
        ValueError: If the signature is invalid.
        stripe.error.SignatureVerificationError: If the webhook secret is wrong.
    """
    if not WEBHOOK_SECRET:
        raise ValueError("STRIPE_WEBHOOK_SECRET is not configured.")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        raise

    event_type = event["type"]
    event_data = event["data"]["object"]

    print(f"[Stripe Webhook] Received: {event_type}")

    try:
        if event_type == "checkout.session.completed":
            print(f"[Stripe Webhook] checkout.session.completed: client_ref={getattr(event_data,'client_reference_id')}, payment_status={getattr(event_data,'payment_status')}")
            _handle_checkout_completed(event_data)
        elif event_type == "customer.subscription.updated":
            print(f"[Stripe Webhook] subscription.updated: id={getattr(event_data,'id')}, status={getattr(event_data,'status')}")
            _handle_subscription_updated(event_data)
        elif event_type == "customer.subscription.deleted":
            print(f"[Stripe Webhook] subscription.deleted: id={getattr(event_data,'id')}")
            _handle_subscription_deleted(event_data)
        elif event_type == "invoice.payment_failed":
            _handle_invoice_payment_failed(event_data)
        elif event_type == "payment_intent.succeeded":
            print(f"[Stripe Webhook] payment_intent.succeeded — ok, but checkout.session handles fulfillment")
        else:
            print(f"[Stripe Webhook] Unhandled event type: {event_type}")
    except Exception as handler_err:
        print(f"[Stripe Webhook] ERROR in handler for {event_type}: {handler_err}")
        import traceback
        traceback.print_exc()
        raise

    return {"received": True, "type": event_type}


# ─── Event Handlers ────────────────────────────────────────────────────────────


def _get(obj, key, default=""):
    """Safely get a value from a StripeObject or dict."""
    try:
        val = getattr(obj, key, None)
        if val is None:
            # Also try dict-style access for raw dicts
            if isinstance(obj, dict):
                return obj.get(key, default)
            return default
        return val
    except Exception:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return default


def _handle_checkout_completed(session):
    """Handle checkout.session.completed — grant PRO access.

    IDEMPOTENCY: We use the stripe_checkout_session_id UNIQUE constraint
    in the payments table. If this session was already processed, the
    UPDATE on payments will be a no-op (or we check first).
    """
    session_id = _get(session, "id")
    user_id_str = _get(session, "client_reference_id")
    if not user_id_str:
        metadata = _get(session, "metadata")
        user_id_str = _get(metadata, "user_id") if metadata else ""
    payment_status = _get(session, "payment_status")

    print(f"[Stripe Webhook] Session {session_id}: user_id={user_id_str}, payment_status={payment_status}")

    if payment_status != "paid":
        print(f"[Stripe Webhook] Payment not complete (status={payment_status}), skipping.")
        return

    if not user_id_str:
        print("[Stripe Webhook] ERROR: No user_id in checkout session — cannot fulfill.")
        return

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        print(f"[Stripe Webhook] ERROR: Invalid user_id in checkout session: {user_id_str}")
        return

    db = get_db()

    # Check if this session was already processed (idempotency)
    cursor = db.execute(
        "SELECT status FROM payments WHERE stripe_checkout_session_id = ?",
        (session_id,),
    )
    row = cursor.fetchone()
    if row and row["status"] == "completed":
        print(f"[Stripe Webhook] Session {session_id} already processed, skipping.")
        return

    # Update payment record to completed
    db.execute(
        """UPDATE payments
           SET status = 'completed',
               stripe_payment_intent_id = ?,
               stripe_subscription_id = ?
           WHERE stripe_checkout_session_id = ?""",
        (
            _get(session, "payment_intent"),
            _get(session, "subscription"),
            session_id,
        ),
    )

    # Get subscription details
    subscription_id = _get(session, "subscription")
    customer_id = _get(session, "customer")

    # Retrieve subscription to get period dates
    current_period_start = None
    current_period_end = None
    if subscription_id:
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            current_period_start = datetime.fromtimestamp(
                sub.current_period_start, tz=timezone.utc
            ).isoformat()
            current_period_end = datetime.fromtimestamp(
                sub.current_period_end, tz=timezone.utc
            ).isoformat()
        except stripe.error.StripeError as e:
            print(f"[Stripe Webhook] Failed to retrieve subscription {subscription_id}: {e}")

    # Create or update membership record
    cursor = db.execute(
        "SELECT id FROM memberships WHERE stripe_subscription_id = ?",
        (subscription_id,),
    )
    existing = cursor.fetchone()
    if existing:
        db.execute(
            """UPDATE memberships
               SET status = 'active',
                   stripe_customer_id = ?,
                   current_period_start = ?,
                   current_period_end = ?,
                   updated_at = ?
               WHERE stripe_subscription_id = ?""",
            (
                customer_id,
                current_period_start,
                current_period_end,
                datetime.now(timezone.utc).isoformat(),
                subscription_id,
            ),
        )
    else:
        db.execute(
            """INSERT INTO memberships
               (user_id, stripe_customer_id, stripe_subscription_id,
                stripe_price_id, status, current_period_start, current_period_end)
               VALUES (?, ?, ?, ?, 'active', ?, ?)""",
            (
                user_id,
                customer_id,
                subscription_id,
                PRO_PRICE_ID,
                current_period_start,
                current_period_end,
            ),
        )

    # Grant PRO access to the user
    db.execute(
        """UPDATE users
           SET is_pro = 1, pro_expires_at = ?, updated_at = ?
           WHERE id = ?""",
        (current_period_end, datetime.now(timezone.utc).isoformat(), user_id),
    )

    db.commit()
    print(f"[Stripe Webhook] PRO access granted to user {user_id} (session {session_id}).")


def _handle_subscription_updated(subscription):
    """Handle customer.subscription.updated — sync subscription status."""
    subscription_id = _get(subscription, "id")
    customer_id = _get(subscription, "customer")
    status = _get(subscription, "status")

    cp_start = _get(subscription, "current_period_start") or 0
    cp_end = _get(subscription, "current_period_end") or 0
    current_period_start = datetime.fromtimestamp(cp_start, tz=timezone.utc).isoformat()
    current_period_end = datetime.fromtimestamp(cp_end, tz=timezone.utc).isoformat()
    canceled_at = None
    canceled_ts = _get(subscription, "canceled_at")
    if canceled_ts:
        canceled_at = datetime.fromtimestamp(canceled_ts, tz=timezone.utc).isoformat()

    db = get_db()

    # Update membership record
    cursor = db.execute(
        "SELECT id, user_id FROM memberships WHERE stripe_subscription_id = ?",
        (subscription_id,),
    )
    row = cursor.fetchone()

    if row:
        db.execute(
            """UPDATE memberships
               SET status = ?, current_period_start = ?, current_period_end = ?,
                   canceled_at = ?, updated_at = ?
               WHERE stripe_subscription_id = ?""",
            (
                status,
                current_period_start,
                current_period_end,
                canceled_at,
                datetime.now(timezone.utc).isoformat(),
                subscription_id,
            ),
        )
        user_id = row["user_id"]
    else:
        # Subscription not linked yet — try to find by customer or create
        logger.warning(f"Subscription {subscription_id} not found in memberships.")
        return

    # Sync user PRO status based on subscription status
    if status in ("active", "trialing"):
        db.execute(
            "UPDATE users SET is_pro = 1, pro_expires_at = ? WHERE id = ?",
            (current_period_end, user_id),
        )
    elif status in ("canceled", "incomplete_expired", "unpaid"):
        db.execute(
            "UPDATE users SET is_pro = 0, pro_expires_at = NULL WHERE id = ?",
            (user_id,),
        )
    elif status == "past_due":
        # Keep PRO for now but mark — Stripe will retry payment
        # If it stays past_due, it eventually becomes canceled/unpaid
        pass

    db.commit()
    logger.info(
        f"Subscription {subscription_id} updated: status={status}, user={user_id}"
    )


def _handle_subscription_deleted(subscription):
    """Handle customer.subscription.deleted — revoke PRO access."""
    subscription_id = _get(subscription, "id")

    db = get_db()
    cursor = db.execute(
        "SELECT user_id FROM memberships WHERE stripe_subscription_id = ?",
        (subscription_id,),
    )
    row = cursor.fetchone()
    if row:
        user_id = row["user_id"]
        db.execute(
            """UPDATE memberships
               SET status = 'canceled', updated_at = ?
               WHERE stripe_subscription_id = ?""",
            (datetime.now(timezone.utc).isoformat(), subscription_id),
        )
        db.execute(
            "UPDATE users SET is_pro = 0, pro_expires_at = NULL WHERE id = ?",
            (user_id,),
        )
        db.commit()
        logger.info(f"PRO access revoked for user {user_id} (subscription deleted).")


def _handle_invoice_payment_failed(invoice):
    """Handle invoice.payment_failed — mark subscription as past_due."""
    subscription_id = _get(invoice, "subscription")
    if not subscription_id:
        return

    db = get_db()
    db.execute(
        """UPDATE memberships
           SET status = 'past_due', updated_at = ?
           WHERE stripe_subscription_id = ?""",
        (datetime.now(timezone.utc).isoformat(), subscription_id),
    )
    db.commit()
    logger.warning(f"Invoice payment failed for subscription {subscription_id}")


# ─── Customer Portal ───────────────────────────────────────────────────────────


def create_portal_session(customer_id: str, return_url: str) -> str:
    """Create a Stripe Customer Portal session for subscription management.

    If customer_id is empty, tries to look it up from the subscription.

    Returns the portal URL to redirect the user to.
    """
    if not customer_id:
        raise ValueError("Customer ID is required. Please ensure your subscription is linked to a Stripe customer.")

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return session.url


def get_customer_id_for_user(user_id: int) -> Optional[str]:
    """Get the Stripe customer ID for a user, looking up via subscription if needed.

    Returns the customer_id string, or None if not found.
    """
    db = get_db()

    # First try: get from memberships table
    cursor = db.execute(
        """SELECT stripe_customer_id, stripe_subscription_id FROM memberships
           WHERE user_id = ? AND stripe_customer_id IS NOT NULL AND stripe_customer_id != ''
           ORDER BY created_at DESC LIMIT 1""",
        (user_id,),
    )
    row = cursor.fetchone()
    if row and row["stripe_customer_id"]:
        return row["stripe_customer_id"]

    # Second try: retrieve customer from subscription
    cursor = db.execute(
        """SELECT stripe_subscription_id FROM memberships
           WHERE user_id = ? AND stripe_subscription_id IS NOT NULL AND stripe_subscription_id != ''
           ORDER BY created_at DESC LIMIT 1""",
        (user_id,),
    )
    row = cursor.fetchone()
    if row and row["stripe_subscription_id"]:
        try:
            sub = stripe.Subscription.retrieve(row["stripe_subscription_id"])
            customer_id = sub.customer
            if customer_id:
                # Save for future use
                db.execute(
                    "UPDATE memberships SET stripe_customer_id = ? WHERE stripe_subscription_id = ?",
                    (customer_id, row["stripe_subscription_id"]),
                )
                db.commit()
                return customer_id
        except stripe.error.StripeError as e:
            print(f"[Stripe] Failed to retrieve subscription for customer lookup: {e}")

    return None


# ─── Session Verification ─────────────────────────────────────────────────────


def verify_checkout_session(session_id: str, user_id: int) -> Optional[dict]:
    """Verify a checkout session after redirect from Stripe.

    Checks that the session belongs to the given user and was paid successfully.
    If payment is complete, also upgrades the user to PRO directly
    (in case the webhook hasn't arrived yet).

    Returns:
        {"status": "paid"|"unpaid", "subscription_id": "...", "is_pro": True/False, ...}
        or None if the session doesn't belong to this user.
    """
    try:
        session = stripe.checkout.Session.retrieve(
            session_id, expand=["line_items"]
        )
    except stripe.error.StripeError as e:
        print(f"[Stripe] Failed to retrieve session {session_id}: {e}")
        return None

    # Security: verify the session belongs to this user
    session_user_id = _get(session, "client_reference_id")
    if str(session_user_id) != str(user_id):
        print(f"[Stripe] Session {session_id} user mismatch: expected {user_id}, got {session_user_id}")
        return None

    payment_status = _get(session, "payment_status") or "unpaid"
    subscription_id = _get(session, "subscription")
    customer_id = _get(session, "customer")

    # If payment is complete, ensure user is upgraded to PRO
    # (This handles the case where webhook hasn't been received yet)
    if payment_status == "paid":
        db = get_db()

        # Check if this session already processed (idempotency)
        cursor = db.execute(
            "SELECT id, status FROM payments WHERE stripe_checkout_session_id = ?",
            (session_id,),
        )
        row = cursor.fetchone()

        if not row or row["status"] != "completed":
            try:
                # Wrap ALL updates in a transaction so we don't partially upgrade
                db.execute("BEGIN")

                # Update or create payment record
                if not row:
                    db.execute(
                        """INSERT INTO payments
                           (user_id, stripe_checkout_session_id, stripe_subscription_id, amount, currency, status)
                           VALUES (?, ?, ?, ?, 'usd', 'completed')""",
                        (user_id, session_id, subscription_id or "", getattr(session, "amount_total", 0) or 499),
                    )
                else:
                    db.execute(
                        """UPDATE payments SET status = 'completed',
                           stripe_subscription_id = ?, stripe_payment_intent_id = ?
                           WHERE stripe_checkout_session_id = ?""",
                        (subscription_id or "", _get(session, "payment_intent") or "", session_id),
                    )

                # Get subscription period
                current_period_start = None
                current_period_end = None
                if subscription_id:
                    try:
                        sub = stripe.Subscription.retrieve(subscription_id)
                        current_period_start = datetime.fromtimestamp(
                            sub.current_period_start, tz=timezone.utc
                        ).isoformat()
                        current_period_end = datetime.fromtimestamp(
                            sub.current_period_end, tz=timezone.utc
                        ).isoformat()
                    except Exception as e:
                        print(f"[Stripe] Could not retrieve subscription {subscription_id}: {e}")

                # Create or update membership
                cursor = db.execute(
                    "SELECT id FROM memberships WHERE stripe_subscription_id = ?",
                    (subscription_id or "",),
                )
                if cursor.fetchone():
                    db.execute(
                        """UPDATE memberships SET status = 'active', stripe_customer_id = ?,
                           current_period_start = ?, current_period_end = ?, updated_at = ?
                           WHERE stripe_subscription_id = ?""",
                        (customer_id, current_period_start, current_period_end,
                         datetime.now(timezone.utc).isoformat(), subscription_id or ""),
                    )
                else:
                    db.execute(
                        """INSERT INTO memberships
                           (user_id, stripe_customer_id, stripe_subscription_id,
                            stripe_price_id, status, current_period_start, current_period_end)
                           VALUES (?, ?, ?, ?, 'active', ?, ?)""",
                        (user_id, customer_id, subscription_id or "",
                         PRO_PRICE_ID, current_period_start, current_period_end),
                    )

                # Grant PRO access
                db.execute(
                    """UPDATE users SET is_pro = 1, pro_expires_at = ?, updated_at = ?
                       WHERE id = ?""",
                    (current_period_end, datetime.now(timezone.utc).isoformat(), user_id),
                )
                db.commit()
                print(f"[Stripe] PRO access granted via session verification for user {user_id}")
            except Exception as e:
                db.execute("ROLLBACK")
                print(f"[Stripe] Failed to upgrade user {user_id}: {e}")
                import traceback
                traceback.print_exc()
            is_pro = True
        else:
            is_pro = True  # Already processed
    else:
        is_pro = False

    return {
        "status": payment_status,
        "subscription_id": subscription_id,
        "customer_id": customer_id,
        "amount_total": getattr(session, "amount_total", 0) or 0,
        "currency": _get(session, "currency") or "usd",
        "is_pro": is_pro,
        "pro_expires_at": None,  # Will be filled by caller
    }
