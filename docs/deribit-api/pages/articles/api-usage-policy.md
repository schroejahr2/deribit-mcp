> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/api-usage-policy",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# API Usage Policy

> Deribit is committed to providing a fast, reliable, and efficient trading platform for all users.

To maintain the integrity and performance of our system, we are introducing new guidelines for API usage. These guidelines are aimed at ensuring that all users have fair access to the platform without unnecessary strain on resources.

These guidelines sit on top of our rate limit policy. Limits are determined at Deribit's discretion. Deribit will not outright ban or limit API usage based on these policies without notice but such penalties can arise in case of non-cooperation.

## Matching Engine requests

List of matching engine requests can be found here: [Rate Limits](/articles/rate-limits).

To avoid unnecessary congestion of the matching engine Deribit monitors user's Order to Volume ratio. The Order to Volume Ratio (OTV) is a metric used to assess the number of orders placed by a trader relative to the actual volume of trades executed. It helps us identify patterns of excessive order placement that might lead to system strain, market manipulation, or inefficiencies within our trading platform.

OTV is defined as:

**OTV = (# ME Changes / Volume)**

A *ME Change* is any change to an order book. This could be an insert, amend or cancellation. Each cancellation done by a mass cancel counts towards the number of ME changes separately. The same is true for quotes. A mass quote that inserts 100 double-sided quotes adds 200 to the limit. Immediate-or-cancel orders (IOCs) and Fill-or-Kill orders (FOKs) that are cancelled count double towards the ME changes, they are seen as an insert and an instant cancellation. Market-maker protection (MMP) and self-match prevention (SMP) triggers are excluded, but are monitored separately. To calculate volume we only consider trades on which the client was the maker. We monitor these ratios per product group and currency.

A healthy OTV ensures that traders are placing orders that have a reasonable likelihood of execution. Monitoring OTV helps us prevent orders that would put unnecessary stress on the system, maintaining a smooth trading experience for everyone.

Traders who consistently exhibit an unusually high OTV may be subject to rate limits. OTV magnitude is determined at Deribit's discretion. As a general rule of thumb we consider OTV ratios higher than 10,000 BTC (10,000 ME changes per 1 BTC of volume traded) or 1,000 ETH high. We will never outright rate limit users for high OTV ratios without proper communication beforehand.

## Non-Matching Engine requests

To clarify the types of API calls that are subject to monitoring, we are grouping them into specific categories:

### 1. Market Data API Calls

To reduce unnecessary load, we encourage users to switch to WebSocket subscriptions wherever possible. WebSocket connections provide a real-time, efficient stream of market data, reducing the need for repeated polling via API which can result in returning duplicate information multiple times.

These endpoints typically carry market information or user trading information. Some examples include:

* `/public/get_order_book`
* `/public/ticker`
* `/private/get_open_orders`

Full list of our websocket subscription coverage can be found here: [Subscription Channels](/subscriptions).

Please note that we also have a limit of 500 channels per subscription.

Excessive usage of these endpoints can result in stricter rate limits.

### 2. Excessive Errors and Failed Requests

Repeatedly sending incorrect or malformed API requests can negatively impact platform performance. Users who consistently send requests that result in high error rates may be subject to additional monitoring. This includes users who exceed rate limits and persist in making the same call resulting in an error.

Excessive errors can result in IP banning. This includes errors produced by exceeding rate limits.

### 3. Protocol Pings

While pings are a necessary part of keeping connections alive, excessive or unnecessary ping requests can consume system resources. We recommend that users minimize the frequency of protocol pings and confirm heartbeat every 30-60 seconds.

Unnecessary protocol calls may result in stricter rate limits.

### 4. Other

We recognize that users need reliable access to their account and market data, including withdrawals, account information, and contract specifications. However, we ask users to refrain from making excessive or redundant calls and ensure that they only request data as needed.

Unnecessary usage of these endpoints may result in stricter rate limits.

### 5. Unauthenticated Requests

Unauthenticated API requests are used to access public information, such as market data, without requiring a user account. We prefer users making authenticated request to our platform even for publicly available information. For this reason our policy is more strict on unauthenticated users.

Unauthenticated requests are more likely to result in an IP ban as we cannot contact the client behind them directly.

If you have any questions or need assistance optimizing your API usage, please reach out to our support team.
