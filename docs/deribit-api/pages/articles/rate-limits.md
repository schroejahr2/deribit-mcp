> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/rate-limits",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Rate Limits

> To maintain fair and stable access to our API, Deribit uses a credit-based rate limiting system.

<Warning>
  <Heading>Exchange-Wide Compliance (OTV & API Usage Policy)</Heading>

  All API traffic—whether authenticated or public—**must follow Deribit's broader trading-integrity rules**, including the **Order-to-Volume (OTV) limits** and other anti-abuse protections. Violations can trigger immediate session disconnects, additional throttling, or stronger enforcement actions.

  For full guidelines, please review our [API Usage Policy](/hc/en-us/articles/25944617449373#UUID-56019658-17b2-b28e-ee98-3335977015d2) (which also covers OTV thresholds and other exchange-abuse rules).
</Warning>

This system ensures efficient use of platform resources while accommodating different trading volumes.

<Note>
  Rate limits described in this article **do not apply to Mass Quotes**. Mass Quotes follow their own dedicated rate-limiting rules, which are documented separately in the [Mass Quotes Specifications article](/articles/mass-quotes-specifications).
</Note>

## Credit-Based System

Each API request consumes a certain number of credits. The refill rate and maximum credit pool for your sub-account depend on your trading activity and tier. **If a request arrives when no credits remain, we immediately send a `too_many_requests` (`code 10028`) or similar error and terminate the session.** After a disconnect, you must wait for credits to replenish and then re-establish a new connection before sending additional requests.

Key elements of this system include:

### Credit Refill

Credits are **replenished continuously at a fixed rate**, depending on your sub-account's tier. This refill acts like a **leaky bucket**: each second, a certain number of credits "drip" back into your sub-account's credit pool. You can think of this as a "credits per second" (CPS) refill rate.

<Note>
  Rate limits are applied [per sub-account](/hc/en-us/articles/25944616386973#UUID-038b9516-2490-c84d-c77a-c8e627bd7b18). Each sub-account has its own independent rate limit.
</Note>

* **Example**: If your refill rate is 20 credits/second, and each request costs 1 credit, you can sustainably send 20 requests per second without depleting your credits.
* The refill continues **even when you're not making requests**, allowing you to accumulate credits back up to your **maximum credit limit**.
* If your maximum credit cap is 200 and your refill rate is 20 credits/sec, it will take 10 seconds to fully refill from 0 to 200.

This refill mechanism helps to:

* Allow **burst activity** (e.g., submitting multiple orders at once), as long as it doesn't exceed the maximum credit limit.
* Encourage **consistent and predictable usage**, minimizing sudden surges that could strain the system.

### Maximum Credits

This is the **upper bound** of your available credit pool. You cannot accumulate more credits than this cap, regardless of how long you wait. It determines the size of request bursts you can make.

### Cost per Request

<Tip>
  Using WebSocket subscriptions for real-time data reduces REST credit consumption.
</Tip>

<Info>
  <Heading>Methods with Non-Default Rate Limits</Heading>

  The following methods have custom rate limits that differ from the standard non-matching engine defaults:

  | Method                                                                                                                                                                                                        | Cost    | Credits | Sustained Rate        | Burst Capacity |
  | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ------- | --------------------- | -------------- |
  | [`public/get_instruments`](https://docs.deribit.com/api-reference/market-data/public-get_instruments)                                                                                                         | 10,000  | 500,000 | 1 request/second      | 50 requests    |
  | [`public/subscribe`](https://docs.deribit.com/api-reference/subscription-management/public-subscribe) [`private/subscribe`](https://docs.deribit.com/api-reference/subscription-management/private-subscribe) | 3,000   | 30,000  | \~3.3 requests/second | 10 requests    |
  | [`private/move_positions`](https://docs.deribit.com/api-reference/trading/private-move_positions)                                                                                                             | 100,000 | 600,000 | 6 requests/minute     | 6 requests     |
  | [`private/get_transaction_log`](https://docs.deribit.com/api-reference/account-management/private-get_transaction_log)                                                                                        | 10,000  | 80,000  | 1 request/second      | 8 requests     |

  These limits are enforced using the same credit-based system as other methods, but with different cost and credit pool configurations.

  <Note>
    **Weekly Usage Limit for [`private/move_positions`](https://docs.deribit.com/api-reference/trading/private-move_positions)**: In addition to the per-minute rate limit, there is a limit of **100 move\_position uses per week (168 hours)**.
  </Note>
</Info>

<Warning>
  <Heading>Webpage Usage Also Consumes API Credits</Heading>

  Please note that using the [Deribit web platform](https://www.deribit.com/futures/BTC-PERPETUAL) also generates API requests behind the scenes. This means **browsing certain pages (e.g., order book, positions, account info)** can **consume credits from your API rate limit**, just like programmatic API calls.

  If you are running automated scripts or trading bots in parallel with an open Deribit web session, you may reach your credit limit more quickly than expected. When this happens, you may receive a `too_many_requests` error (code `10028`), even if your script appears to be within the expected request volume.

  To optimize performance:

  * **Avoid keeping multiple browser tabs open** on data-intensive pages.
  * Consider logging out of the web interface when running high-frequency strategies.
  * **Note**: If you customize a trading page by adding more components, that may affect the rate limit.
</Warning>

## Matching vs Non-Matching Engine Requests

There are two main categories of API requests:

* **Matching engine requests**: These interact with the order book, such as placing or cancelling an order.
* **Non-matching engine requests**: These involve general queries, such as retrieving account information or market data.

Each type of request consumes credits at a different rate.

### Default Settings for Non-Matching Engine Requests

* **Cost per Request**: 500 credits.
* **Maximum Credits**: 50,000 credits.
* **Refill Rate**: Credits are refilled at a rate that allows up to 20 requests per second (10,000 credits per second).
* **Burst Capacity**: Allows up to 100 requests at once, considering the maximum credit pool.

#### Burst and Refill Example (non-matching defaults)

<Warning>
  All rate-limit values in this example are illustrative only. They describe how the mechanism works and do not represent your actual limits.
</Warning>

* The burst counter starts with **50,000 credits** (the maximum pool).
* Each request costs **500 credits**; 100 back-to-back requests would fully drain the pool if you ignore refills.
* Credits **refill continuously** at **10 credits per millisecond** (10,000 per second) even while you are bursting.
* If credits reach zero, new requests fail with `too_many_requests` (code `10028`).
* Sustained traffic at **20 req/s** (20 × 500 = 10,000) matches the refill rate, so the pool stays stable. A rapid **100+ request burst** can still trigger `10028` if it outpaces the current credits.
* If you hit `10028` and need to cancel orders, waiting \~**50 ms** restores \~**500 credits** (10 credits/ms), enough to send a mass-cancel.

### Matching Engine Requests

Each sub-account has an hourly updated rate limit, applicable across all books. Users can check their current rate limits via the [`private/get_account_summary`](https://docs.deribit.com/api-reference/account-management/private-get_account_summary) method.

| Tier Level | 7-Day Trading Volume | Sustained Rate Limit (Requests/Second) | Burst Rate Limit     | Description                                                                                                                |
| ---------- | -------------------- | -------------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Tier 1     | Over USD 25 million  | 30 requests/second                     | 100 requests (burst) | Suitable for high-volume traders, allowing up to 100 requests in a rapid burst or a steady rate of 30 requests per second. |
| Tier 2     | Over USD 5 million   | 20 requests/second                     | 50 requests (burst)  | Designed for medium-volume traders, permitting up to 50 requests in a burst or 20 requests per second.                     |
| Tier 3     | Over USD 1 million   | 10 requests/second                     | 30 requests (burst)  | Appropriate for active traders, enabling up to 30 requests in a burst or 10 requests per second.                           |
| Tier 4     | Up to USD 1 million  | 5 requests/second                      | 20 requests (burst)  | For regular traders, allowing up to 20 requests in a burst or a steady rate of 5 requests per second.                      |

### Automatic Rate Limit Updates

* We recalculate limits **every hour**. There is no “volume/7 per day” delay—the most recent 7-day trading volume is evaluated each hour for every sub-account that has trading stats.
* **Volume window**: the trailing **7-day** trading volume determines your tier. Each hourly recalculation uses the latest 7-day sum.
* **Upgrades**: if your 7-day volume crosses a higher-tier threshold during an hourly check, we immediately move you to that tier (we can skip intermediate tiers; e.g., jumping from Tier 1 straight to Tier 4 is possible).
* **Downgrades**: during an hourly check, if your 7-day volume falls below your current tier’s threshold after being above it in the prior hour, the limits are lowered accordingly. This can also skip tiers if the 7-day volume drops multiple thresholds.

<Info>
  <Heading>Public Access Limitations</Heading>

  Public, **non-authorized** API requests are rate-limited on a **per-IP basis**—they do not draw from the sub-account-level credit pool. If an IP exceeds its public request allowance, subsequent calls may be **temporarily rejected** or the connection **disconnected** to protect platform stability.

  Whenever possible, use **authorized requests tied to your API key**. Authenticated traffic benefits from:

  * **Higher and more transparent limits** that scale with your sub-account's tier.
  * **Client-ID visibility**, letting us distinguish heavy legitimate usage from abusive traffic—so rather than an immediate block, we can apply graduated safeguards if your limit is exceeded.

  In short, authorized requests are always the safer, more reliable option for sustained or high-frequency access.
</Info>

<Info>
  Production and [Testnet environment](/document/preview/12390#UUID-f5f86659-ba8b-6f75-5208-2f751bee1531) operate **on separate, independently-tracked rate-limit pools**. **Limits are not shared** between environments—exceeding Testnet limits will not affect your Production credits, and vice-versa.
</Info>

## Checking current rate limits

Users can access the current rate limits by calling the [`private/get_account_summary`](https://docs.deribit.com/api-reference/account-management/private-get_account_summary) method and receiving `limits` field in response. The configuration of rate limits can be either on a per-currency basis or a default set applied globally across all currencies. Per-currency limits are not the default setting and are enabled only for specific clients upon request.

<Note>
  Per-currency rate limits currently are used **exclusively to decrease** access limits for specific currencies when needed. They are not applied to increase rate limits.
</Note>

### Limits field

`non_matching_engine`: Describes rate limits applicable to requests that do not involve the matching engine. Defined by:

* `burst`: The maximum number of requests permitted in a short burst.
* `rate`: The sustained number of requests allowed over time.

`matching_engine`: Outlines rate limits related to operations that utilize the matching engine, with the following structure:

### Common Limits for All Configurations

#### Spot and Cancel Limits

* `spot`: Applies to spot trading between two different currencies.
* `cancel_all`: Used when canceling all orders globally or by label without specifying a currency.

### Global vs. Per-Currency Limits

* When `limits_per_currency` = `false`, limits apply globally:
  * `trading`: Overall trading operations
  * `maximum_quotes`: Total number of quotes
  * `maximum_mass_quotes`: Mass quoting operations
  * `guaranteed_mass_quotes`: Guaranteed mass quotes

* When `limits_per_currency` = `true`, limits are set **per settlement currency** under the `matching_engine` object:
  * Each currency key includes:
    * `trading`: Per-currency trading limits
    * `maximum_quotes`: Per-currency quote limits
    * `maximum_mass_quotes`: Per-currency mass quoting limits
    * `guaranteed_mass_quotes`: Per-currency guaranteed mass quotes

### Cancel Method Logic

* [`private/cancel_all`](https://docs.deribit.com/api-reference/trading/private-cancel_all): Uses the global `cancel_all` limit.
* [`private/cancel_all_by_currency`](https://docs.deribit.com/api-reference/trading/private-cancel_all_by_currency) / [`private/cancel_all_by_instrument`](https://docs.deribit.com/api-reference/trading/private-cancel_all_by_instrument): Applies the relevant trading or spot limit for the specified currency or instrument.
* [`private/cancel_all_by_kind_or_type`](https://docs.deribit.com/api-reference/trading/private-cancel_all_by_kind_or_type):
  * No currency specified → uses cancel\_all
  * Specific currency → uses per-currency trading limit
  * Spot instrument → uses spot limit

**Example for users without per currency config (default):**

```json theme={null}
{
  "non_matching_engine": {
    "burst": 1500,
    "rate": 1000
  },
  "limits_per_currency": false,
  "matching_engine": {
    "trading": {
      "total": {
        "burst": 20,
        "rate": 5
      }
    },
    "spot": {
      "burst": 250,
      "rate": 200
    },
    "maximum_quotes": {
      "burst": 500,
      "rate": 500
    },
    "maximum_mass_quotes": {
      "burst": 10,
      "rate": 10
    },
    "guaranteed_mass_quotes": {
      "burst": 2,
      "rate": 2
    },
    "cancel_all": {
      "burst": 250,
      "rate": 200
    }
  }
}
```

**Example for users with per currency config:**

```json theme={null}
{
  "non_matching_engine": {
    "burst": 1500,
    "rate": 1000
  },
  "limits_per_currency": true,
  "matching_engine": {
    "cancel_all": {
      "burst": 250,
      "rate": 200
    },
    "spot": {
      "burst": 250,
      "rate": 200
    },
    "usdt": {
      "maximum_quotes": {
        "burst": 500,
        "rate": 500
      },
      "maximum_mass_quotes": {
        "burst": 10,
        "rate": 10
      },
      "guaranteed_mass_quotes": {
        "burst": 2,
        "rate": 2
      },
      "trading": {
        "total": {
          "burst": 250,
          "rate": 200
        }
      }
    },
    "usdc": {
      "maximum_quotes": {
        "burst": 500,
        "rate": 500
      },
      "maximum_mass_quotes": {
        "burst": 10,
        "rate": 10
      },
      "guaranteed_mass_quotes": {
        "burst": 2,
        "rate": 2
      },
      "trading": {
        "total": {
          "burst": 250,
          "rate": 200
        }
      }
    },
    "eth": {
      "maximum_quotes": {
        "burst": 500,
        "rate": 500
      },
      "maximum_mass_quotes": {
        "burst": 10,
        "rate": 10
      },
      "guaranteed_mass_quotes": {
        "burst": 2,
        "rate": 2
      },
      "trading": {
        "total": {
          "burst": 250,
          "rate": 200
        }
      }
    },
    "btc": {
      "maximum_quotes": {
        "burst": 500,
        "rate": 500
      },
      "maximum_mass_quotes": {
        "burst": 10,
        "rate": 10
      },
      "guaranteed_mass_quotes": {
        "burst": 2,
        "rate": 2
      },
      "trading": {
        "perpetuals": {
          "burst": 20,
          "rate": 10
        },
        "total": {
          "burst": 150,
          "rate": 100
        }
      }
    }
  }
}
```

## Matching Engine Requests Overview

All requests **not listed below** are treated as **non-matching engine** requests.

* [`private/buy`](https://docs.deribit.com/api-reference/trading/private-buy)
* [`private/sell`](https://docs.deribit.com/api-reference/trading/private-sell)
* [`private/edit`](https://docs.deribit.com/api-reference/trading/private-edit)
* [`private/edit_by_label`](https://docs.deribit.com/api-reference/trading/private-edit_by_label)
* [`private/cancel`](https://docs.deribit.com/api-reference/trading/private-cancel)
* [`private/cancel_by_label`](https://docs.deribit.com/api-reference/trading/private-cancel_by_label)
* [`private/cancel_all`](https://docs.deribit.com/api-reference/trading/private-cancel_all)
* [`private/cancel_all_by_instrument`](https://docs.deribit.com/api-reference/trading/private-cancel_all_by_instrument)
* [`private/cancel_all_by_currency`](https://docs.deribit.com/api-reference/trading/private-cancel_all_by_currency)
* [`private/cancel_all_by_kind_or_type`](https://docs.deribit.com/api-reference/trading/private-cancel_all_by_kind_or_type)
* [`private/close_position`](https://docs.deribit.com/api-reference/trading/private-close_position)
* [`private/verify_block_trade`](https://docs.deribit.com/api-reference/block-trade/private-verify_block_trade)
* [`private/execute_block_trade`](https://docs.deribit.com/api-reference/block-trade/private-execute_block_trade)
* [`private/move_positions`](https://docs.deribit.com/api-reference/trading/private-move_positions)
* [`private/mass_quote`](https://docs.deribit.com/api-reference/trading/private-mass_quote)
* [`private/cancel_quotes`](https://docs.deribit.com/api-reference/trading/private-cancel_quotes)
* [`private/add_block_rfq_quote`](https://docs.deribit.com/api-reference/block-rfq/private-add_block_rfq_quote)
* [`private/edit_block_rfq_quote`](https://docs.deribit.com/api-reference/block-rfq/private-edit_block_rfq_quote)
* [`private/cancel_block_rfq_quote`](https://docs.deribit.com/api-reference/block-rfq/private-cancel_block_rfq_quote)
* [`private/cancel_all_block_rfq_quotes`](https://docs.deribit.com/api-reference/block-rfq/private-cancel_all_block_rfq_quotes)

## FIX Message Types

* [`new_order_single`](https://docs.deribit.com/fix-api/production/new-order-single)
* [`order_cancel_request`](https://docs.deribit.com/fix-api/production/order-cancel-request)
* [`order_mass_cancel_request`](https://docs.deribit.com/fix-api/production/order-mass-cancel-request)
* [`order_cancel_replace_request`](https://docs.deribit.com/fix-api/production/order-cancel-replace)
* [`mass_quote`](https://docs.deribit.com/fix-api/production/mass-quote)
* [`quote_cancel`](https://docs.deribit.com/fix-api/production/quote-cancel)
