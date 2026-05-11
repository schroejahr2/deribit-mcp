> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/order-management-best-practices",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Order Management

> Efficient order management is crucial for high-performance trading on Deribit.

This article explains how orders are processed through Deribit's system and outlines best practices to achieve the fastest and most reliable execution. We cover the order submission pipeline, internal queues, latency optimization, cancellation strategies, order editing vs. replacing, advanced order types (like OCO/OTO), and other tips for developers and institutional traders using the Deribit API. The goal is to help you manage orders effectively while minimizing latency and avoiding common pitfalls.

## Order Submission Architecture

When you send an order to Deribit (whether via REST API, WebSocket, or FIX), it travels through a multi-node architecture before reaching the matching engine. Deribit's trading platform is built in Erlang and uses several gateway nodes that accept client connections and requests. These gateway nodes are shared among all participants; a load balancer assigns your session to a node based on load and network location. Each node communicates with a central master node or matching engine cluster to determine the state of orders and execute trades. Your order goes from the client, into one of Deribit's API gateway nodes and then into the matching engine where it is matched against other orders.

<Info>
  All API interfaces (REST, WebSocket, FIX) ultimately feed into the same matching engine. Using WebSocket or FIX provides a persistent connection to these nodes, whereas REST establishes a new HTTP connection per request. The multiple gateway nodes ensure scalability and load distribution, but they do not alter the fairness of matching – all orders meet at the single matching engine for execution.
</Info>

## Order Processing Queues

Along the path from your system to the matching engine, orders may queue at several stages. Understanding these queues can help in optimizing performance:

### Client-Side and TCP Queue

First, your order may sit briefly in the TCP send buffer of your connection. This is a client-specific queue and is not shared with other participants. High network latency or sending large bursts of data can cause this to build up.

### Deribit Entry Node Queues

Within the Deribit node that received your order, there are separate thread pools for different request types. For example, "public" data requests (like market data subscriptions) may use a shared pool, while "private" actions (like placing or cancelling orders) use a different pool. Private order requests from your session typically go into a queue dedicated to your connection (not shared with others), whereas certain public feeds are processed in shared queues. This design prevents, for instance, a slow public feed from blocking your private order commands.

### Inter-Node Communication

If the gateway node needs to communicate with the master matching engine or other nodes (using Erlang's distribution protocol), those messages go through an internal TCP channel. This inter-node channel can be considered shared in the sense that messages from many participants might flow through it, potentially queuing under high load.

### User-Level Lock Queue

At the matching engine layer, Deribit enforces an ordering for actions per user per currency. All requests that affect a single user's account for a given currency are funneled through a user process lock. This means if you send multiple actions (orders, cancels) on the same account and same currency, they will be executed sequentially in the order they were received. If you have multiple connections (or API keys) on the same account trading the same currency, they still share this queue for consistency. This queue is shared among all connections of that user for that currency.

### Matching Engine Queue

Finally, each instrument's order book process has its own queue for incoming orders and cancels. This is where your order ultimately competes with others. This is shared by all participants trading that instrument – only one action can be processed at a time per order book. If many orders arrive around the same time, they will queue here briefly before being matched in sequence.

In summary, some queues (like your connection's TCP and private worker queue) are exclusive to you, while others (like the global order book) are naturally shared. Knowing this, you can see why sometimes there may be slight delays or non-deterministic ordering if the system is under heavy load – for example, if a lot of messages hit the same instrument's book at once.

## Concurrency and Request Pipelining

Deribit's API is asynchronous and multi-threaded, which means requests can be handled out of order and in parallel when possible. The platform effectively pipelines different types of requests to maximize throughput. For instance, there are separate internal workers for different categories of actions on a WebSocket connection: one for private matching-engine actions on BTC, another for private actions on ETH (and similarly for other currencies), another for non-matching-engine private requests (like account queries), and another for public data subscriptions. Because of this separation, requests sent back-to-back might be processed concurrently if they belong to different categories.

### Out-of-order responses

It is normal to receive responses in a different order than you sent the requests. For example, if you quickly send a subscription request (public data) followed by an order placement (private trading action), you might see the subscription reply arrive before the order confirmation, even though you sent the order first. This is due to the requests being handled by different worker threads and does not indicate any issue. Deribit's architecture ensures each category (and each currency's orders) are processed in parallel, so the fastest reply wins. In one example, a user noted that a subscription response arrived before an earlier request's response – this is expected behavior under the multi-threaded design.

### Race conditions between participants

In a high-frequency environment, two participants might race to exploit an opportunity. Who wins this race depends largely on external factors (network latency, message timing) and a bit of luck in scheduling. From the moment an order reaches the platform and enters the matching engine, all users' orders are treated fairly in a first-come-first-served manner. However, in a distributed, multi-node system, there is some non-determinism in which order arrives first if they are extremely close in time. A slightly slower participant could get their order matched first if the faster one experienced more network delay or if thread scheduling caused a brief reorder. Essentially, there is no guarantee that the participant who intended to be first always will be – the actual winner is whoever's request makes it through the pipeline to the matching engine first, which can vary in a parallel processing environment.

### Cancelable queued requests

One advanced feature of Deribit's WebSocket API is the ability to cancel or override requests that are still in your session's queue. For example, if you fire off a burst of orders and then send a `cancel_all` command, the system will not only cancel orders that have reached the order book, but also those still waiting in your connection's queue (if any). Those canceled-before-execution requests will return an error with code 13666 ("request\_cancelled\_by\_user"), indicating that the request never hit the order book because you cancelled it in-flight. Similarly, `cancel_by_label` can cancel a specific subset of queued orders by label before they execute. This mechanism helps prevent a backlog of orders from executing if they are no longer needed – effectively giving you control to purge your own queue.

<Note>
  The error code 13666 is not a bad sign; it explicitly tells you that a pending request was successfully withdrawn. In practice, you might see this if you send a batch of orders and then quickly cancel-all – some of those orders might get cancelled before they even hit the matching engine, returning the cancellation error for those specific requests.
</Note>

## Latency Best Practices

Speed is often critical. Here are some best practices to get your orders to the matching engine as quickly as possible:

<AccordionGroup>
  <Accordion title="Use WebSocket or FIX instead of REST">
    WebSocket (JSON-RPC) and FIX connections are persistent and optimized for low-latency, whereas REST incurs extra overhead per request. In fact, WebSocket and FIX offer almost identical latency in most cases. FIX can be marginally faster for certain actions like mass cancels because it bypasses some queueing, but it comes with fewer features compared to WebSockets. REST, on the other hand, is slightly slower since each HTTP request must be set up, authorized, and processed individually. Bottom line: if you are submitting frequent orders or need realtime speed, prefer WebSocket or FIX. Use REST only for infrequent requests or if simplicity is more important than speed.

    <Card title="Protocol Overview" icon="code" href="/articles/json-rpc-overview">
      Learn about JSON-RPC protocol and transport options
    </Card>
  </Accordion>

  <Accordion title="Maintain a lightweight connection">
    Avoid sending or receiving an excessive amount of data on the same connection, as large bursts can fill up the TCP pipeline and JSON parser. For example, if you subscribe to every tick for hundreds of instruments on the same WebSocket you use for trading, the flood of incoming data could delay processing of your order messages. It can be wise to separate heavy market data subscriptions onto a different connection from your order entry, or at least throttle the volume of data.

    <Card title="Connection Management" icon="network-wired" href="/articles/connection-management-best-practices">
      Best practices for managing WebSocket connections
    </Card>
  </Accordion>

  <Accordion title="Send modest bursts of orders">
    If you need to submit many orders, avoid firing extremely large batches all at once. While Deribit's pipelining can process high volumes, sending "tens of orders at once" in a single burst on the same instrument or currency can create a backlog, increasing latency for later orders (a "snowball effect"). Instead, consider staggering batches slightly or using multiple connections (or threads) for very large submissions, splitting them by instrument or currency where possible.

    For high-frequency market making, the Mass Quotes functionality offers a more efficient approach. Instead of sending many individual order placement requests, Mass Quotes lets you submit or update multiple bid/ask pairs for one or more instruments in a single API call. This reduces per-order overhead, lowers network traffic, and helps keep latency low even when quoting across many strikes or maturities.

    Remember that within a single currency, requests are serialized per user. Sending 50 orders for BTC in one go will queue them in sequence; Mass Quotes or careful pacing can help you achieve the same quoting objectives with less queue buildup and faster overall turnaround.

    <Card title="Mass Quotes" icon="quote-left" href="/articles/mass-quotes-specifications">
      Learn about Mass Quotes for efficient market making
    </Card>
  </Accordion>

  <Accordion title="Optimize network conditions">
    Ensure your trading server has a fast, reliable network path to Deribit's servers. If you are latency-sensitive, consider hosting in a location close to Deribit's data center (London LD4 for the main exchange). External internet connections pass through load balancers and have longer routes, adding a bit of latency (on the order of microseconds for the LB hop, plus any geographic delay). Some firms opt for colocation to reduce round-trip time. While this is an infrastructure consideration beyond the API itself, it's a significant factor in race scenarios.
  </Accordion>
</AccordionGroup>

By following these practices – using the right protocol, managing your connection load, and optimizing networking – you can minimize the time it takes for your orders to reach the matching engine.

## Risk Checks

Every order that modifies a portfolio (new orders, edits, closing positions, etc.) must first pass a risk check. This process ensures that balances, positions, and margins remain consistent across the platform. Risk checks are executed inside the Portfolio Queue, where each request waits for a "lock" before the portfolio state can be updated.

### When risk checks may take longer

Risk checks are normally fast, but several factors can extend their processing time:

* **Large portfolios** — A very high number of open positions increases the incremental portfolio updates and synchronization needed.
* **High order activity** — A large amount of active open orders leads to heavier margin calculations.
* **Queue congestion** — If many connections and requests are waiting for portfolio access, checks may be delayed.

### Order types and risk checks

All order types are processed with the same risk checks. Reduce-only flags or time-in-force instructions (e.g., GFD, IOC) do not affect speed.

Cancel requests (`cancel`, `cancel_all`, `cancel_by_label`) also go through the Portfolio Queue, but they are executed without risk checks.

Mass Quotes are the one exception — they skip most risk checks to support high-performance quoting.

### Errors related to risk checks

* **10047 matching\_engine\_queue\_full**: The Portfolio Queue can hold up to 8 waiting processes. If it is full, new requests will be rejected with this error. In FIX this appears as too many requests.
* **10050 lock\_time\_exceeded**: If a request cannot complete the lock procedure within 5 seconds, it times out, even if fewer than 8 processes are waiting.

<Tip>
  **Best practices:**

  * Keep the number of simultaneous client connections below the maximum of 8 to minimize the chance of hitting error 10047.
  * Be aware that internal actions (trigger orders, liquidation orders, advanced option orders) also consume queue slots, leaving fewer available for client activity.
</Tip>

## Order Cancellation Strategies

Managing open orders efficiently often involves bulk cancellations, especially for market makers or algorithmic traders who need to update quotes rapidly. Deribit provides several API endpoints to cancel orders, each suited for different scenarios:

* **Cancel a single order**: You can cancel by order ID using the `private/cancel` method (providing the specific `order_id`). This is straightforward for one-off cancellations.

* **Cancel by label**: If you tag your orders with a label (a user-defined string up to 64 chars) when placing them, you can cancel all orders with that label in one call via `private/cancel_by_label`. This is useful to group and manage related orders. For example, you might label all orders from a particular strategy or instrument and then cancel them in one go by label.

* **Cancel all orders**: `private/cancel_all` will attempt to cancel every open order in your account, across all instruments and currencies. While convenient, this is the heaviest cancel call because it covers everything.

* **Cancel all in a currency**: `private/cancel_all_by_currency` is a more targeted mass cancel – it will cancel all orders in a given currency (e.g., all BTC orders, or all ETH orders). You can even filter by instrument kind or order type if needed (for instance, only options, or only stop orders).

* **Cancel all in an instrument**: `private/cancel_all_by_instrument` will cancel all orders for a specific instrument (e.g., a particular option or future).

* **Cancel quotes via Mass Quotes**: If you are quoting multiple instruments using the Mass Quotes feature, you can cancel all active quotes in a single API call (`private/cancel_quotes`). This is more efficient than cancelling each quoted order individually and is particularly useful for market makers managing large, multi-instrument quoting books.

<Tip>
  **Which is fastest?**

  In terms of raw latency, a cancel by currency tends to be faster than a global cancel-all. This is because when you call the generic `cancel_all`, the system internally splits it into separate cancellations per currency (one for BTC, one for ETH, etc.) plus some overhead.

  If you know you only need to cancel orders in, say, BTC and ETH, it can be quicker to call `private/cancel_all_by_currency` twice (once for BTC, once for ETH) in parallel. This eliminates the extra splitting logic and focuses the cancel requests directly. The result is lower latency for mass canceling, which can be crucial during fast market moves.
</Tip>

Below is an example of using the JSON-RPC API (over WebSocket or HTTP) to cancel all orders for BTC instruments:

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 42,
  "method": "private/cancel_all_by_currency",
  "params": {
    "currency": "BTC"
  }
}
```

The response will indicate how many orders were successfully cancelled. For instance, a result of `{"result": 3}` means three orders were cancelled. You could call this for each currency you trade. Always handle the possibility that some orders might have already filled or been cancelled; those will simply be skipped.

## Order Editing vs. Cancel & Replace

When you need to change an open order's parameters (price or size), you generally have two choices: edit the order in place, or cancel and place a new order. Deribit's API supports editing orders, and it is usually more efficient than canceling and resubmitting a new order.

### Performance advantage

An edit is a single request to the system, whereas cancel + new order is two requests. Fewer requests mean less overhead in your API queue and less work for the matching engine. In practice, editing an order tends to be faster and results in less latency between the change being initiated and the order reflecting the new parameters. It also reduces load on your connection and on Deribit's infrastructure (parsing, queueing, etc.), which is beneficial during high throughput periods.

### Order book priority

If you decrease the order's quantity or keep the price the same, an edit will not change the order's priority in the book – it retains its time priority at that price level. Similarly, if you are only reducing size, you keep your place in the queue for the remaining quantity. In contrast, if you cancelled and placed a new order, you would lose your original queue position entirely; the new order would be considered fresh at the back of the queue for that price.

<Info>
  If you increase the order quantity or change the price (making it either more aggressive or more passive), the edited order is treated akin to a new order at that price level, meaning it will go to the end of the queue for the new price. (This is logical since other orders were already resting at that price.) Importantly, if you edit just the price, even to improve it (e.g., moving a buy up or a sell down), you forfeit the time priority because the order is essentially relocating to a different spot in the book.
</Info>

### Partial fill considerations

Editing preserves the history of any fills. If an order was partially filled before the edit, those fills remain accounted. The cumulative filled amount stays the same, and the remaining size is simply adjusted based on the new total quantity.

For example, suppose you had an order for 200 units, and 100 were filled, leaving 100 unfilled. If you edit the order to increase the total amount to 400, the filled 100 remains part of the order's history, and the remaining quantity is updated to 300. The previous fills are not "reset" when editing an order.

If instead you cancelled the remaining 100 and placed a new order for 300, the new order would have no record of the earlier 100 fill and would receive a new ID and timestamp. Editing is often cleaner for accounting purposes, especially when you need to calculate average fill prices or fees for that order.

### Conclusion

Whenever possible, prefer editing an order over canceling and recreating it, as long as your change falls within what's allowed (e.g., you cannot change a limit order into a stop order via edit; it's meant for price/amount adjustments). Deribit's `private/edit` (by `order_id`) or `private/edit_by_label` (if you use label) can be used for this purpose. Below is an example of editing an order by its label:

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 123,
  "method": "private/edit_by_label",
  "params": {
    "instrument_name": "BTC-PERPETUAL",
    "label": "my_order_group",
    "price": 50111.0,
    "amount": 150
  }
}
```

In this example, we target the order identified by label "my\_order\_group" and change its price to 50111.0 and quantity to 150. The response will return the updated order details (new price, remaining amount, etc.). Use `private/edit` with an `order_id` if you track orders by their IDs instead of labels.

## Partial Fills and Cancellation Notifications

It's important to understand how Deribit notifies you of order events, especially in cases of partial fills. A common point of confusion is seeing an order cancelled notification and an order filled notification for the same order. How can one order be both filled and cancelled?

This happens when an order is partially filled and then the remainder is cancelled. For example, say you posted a sell order for 1000 contracts. It immediately got a partial fill for 500, leaving 500 unfilled. If you then cancel the order, what remains (500) is removed from the book. You will receive:

* One or more trade or fill events for the 500 that traded (via the `user.trades.*` channel or execution reports).
* An order cancellation event indicating the order is no longer active (via the `user.orders.*` channel).

Interpreting a fill notification together with a cancel notification for the same order means recognizing that the order was partially executed and the remaining quantity was removed from the book. Such an order is neither fully filled nor still open; it was partially completed and then closed.

Trading systems should always be designed to process both trade notifications and order updates to maintain accurate tracking of positions and order states, ensuring the ability to decide whether further action is required. A cancel in this context does not undo any executed trades but prevents further execution of the remaining quantity, and an order should not be assumed to be all-or-nothing unless it was placed with a specific instruction such as Fill-Or-Kill.

## Price Band Protections

To protect against erroneous orders or extreme price movements, Deribit employs trading price bandwidth limits on all instruments. This defines an upper and lower bound around a reference price (often the index or last trade price) within which orders can be placed. If you submit an order with a price outside this permitted range, it will be rejected with an error like `price_too_high` or `price_too_low`.

**What to do**: If you encounter these errors, check that your pricing logic is correct. It may be that your price source is stale or you had a bug. If you intentionally want to place an order outside the normal trading range (maybe as a deep stop or extreme hedge), you simply cannot – you'll need to monitor the market until that price comes into range. This mechanism is there to guard all participants from flash crashes or wild prints due to outlier orders.

For more detailed information on price bandwidths, refer to the instrument specifications in Deribit's Knowledge Base. Bandwidth limits can vary between different instrument kinds, so it is important to review the specifications for each product you trade.

## Post-Only Orders and Price Adjustments

Deribit offers a "Post-Only" option on orders, which is a common feature for avoiding taker fees or undesired executions. A Post-Only order will only place liquidity; it will never take liquidity from the order book. If you submit a post-only order that would immediately match against an existing order (thus making you a taker), Deribit will adjust or reject it based on settings:

### Default behavior (price adjustment)

By default, if a post-only order would cross the spread and execute, Deribit will automatically adjust the price to just one tick inside the spread to ensure it becomes a maker order. For example, suppose the best ask is 10,000 and you submit a buy order with `post_only` at 11,000. Instead of filling at 10,000, the system will place your order at \$9,999.50 (assuming a \$0.50 tick) – just below the best ask – so that it rests in the book without executing. This behavior ensures your post-only intent is honored by price sliding.

### Reject mode

If you prefer the order to be strictly not executed and not adjusted, you can enable the post-only reject feature. In the JSON API this is done with `"reject_post_only": true` (and in FIX, by using ExecInst 6A instead of 6). With this setting, if your post-only order would cause an immediate match, the system will reject the order rather than adjusting the price. This gives you more control, as the order either places unmodified at your price (with no match) or it fails. Some traders use this to avoid even the slight difference in price, preferring an outright rejection if the order isn't purely adding liquidity.

### Editing post-only orders

If you edit an existing post-only order in a way that makes it aggressive (for instance, moving its price to a level that would execute against the current book), the behavior depends on the mode:

* In standard post-only mode, the system will adjust the price on edit to remain a maker (similar to initial placement).
* In reject mode (ExecInst 6A / `reject_post_only : true`), the edit request will cause the order to cancel if it would otherwise turn into a taker. Essentially, the order won't persist if your change would violate post-only conditions.

Post-only orders are very useful for market making and ensuring you don't take liquidity inadvertently. Just be aware of the price sliding behavior so you're not surprised by an order resting at a slightly different price than you requested. If you need the exact price or nothing, use the reject mode.

## Iceberg Orders

An Iceberg order allows you to place a large order while only showing a small portion (the `display_amount`) in the order book. Once the visible portion is filled, the system automatically replenishes it (up to the refresh amount) until the total order size is executed or cancelled. The visible part behaves like a maker order, while the hidden portions that trade are treated as takers for fee purposes.

When placing or editing an order using API (`private/buy`, `private/sell`, or `private/edit`), include:

* `display_amount` — the visible tip of the order.
* `refresh_amount` — the fixed amount used to replenish the visible portion when it is filled.

Both parameters are optional, but if `display_amount` is set, it must meet these requirements:

* At least 100 × the instrument's minimum order size.
* At least 1% of the total order size.

### Additional Notes

* The `refresh_amount` remains constant; only the `display_amount` changes as the order is filled.
* Hidden portions execute immediately when matched and incur taker fees.
* Iceberg orders are useful for executing large trades discreetly without revealing the full size to the market.

<Warning>
  Iceberg orders are not supported on future spreads.
</Warning>

## Linked Orders (OTO, OCO, OTOCO)

Deribit allows linking orders together with conditional relationships, which can be extremely useful for automating complex strategies. The primary linked order types are:

### OTO – One-Triggers-Other

This involves a primary order and one or more secondary orders that lie dormant until the primary order executes. When the primary order fully or partially fills (depending on the trigger condition), it triggers the secondary order(s) to be placed. For example, you want to buy 100 BTC-PERP if price drops to \$20,000, and if that order fills, you want to immediately place a take-profit sell order at \$22,000. This is a one-triggers-other setup: your buy is the primary; the sell is secondary and will only enter the book after your buy executes.

### OCO – One-Cancels-Other

This links two orders such that if one order executes, the other is automatically cancelled. A common use case is bracketing the market with a stop loss and take profit. You might have a stop-market order to sell if price falls to \$19,000 and a limit sell order to take profit at \$22,000, both for the same position size. You only want one of them to eventually hit – whichever comes first cancels the other. These two orders would be linked as OCO. If the stop triggers and fills, the take profit is canceled, and vice versa.

### OTOCO – One-Triggers-One-Cancels-Other

This is essentially combining OTO and OCO. You have a primary order, and upon its execution it triggers two secondary orders which are themselves in an OCO relationship. This is the classic entry with bracket exit scenario. For instance, you enter a long position (primary order). When it fills, it triggers placing a stop loss order and a take profit order simultaneously (the two secondaries). Those two secondaries are OCO-linked to each other, so only one can eventually execute – if the profit target hits, the stop is canceled, or if the stop hits, the profit order is canceled. OTOCO thus automates the full cycle: entry, with a protected exit either way. It's very useful for hands-off trading, ensuring that risk is managed and profits are taken without manual intervention.

These linked orders let you set up complex logic server-side. You don't have to watch for your primary order to fill and then manually send the secondaries – the platform will do it for you in a single atomic setup. It's particularly valuable for strategies where immediate reaction is needed (like entering a position with predetermined exit conditions).

## Linked Order Fill Conditions

When using linked orders, you have control over the fill condition that triggers the secondary orders (or cancellations, in the case of OCO). Deribit supports a few modes for how and when the linkage is activated:

### First Hit

The moment any portion of the primary order executes (even a partial fill), the condition triggers. In a First Hit setting:

* **For OTO**: A partial fill of the primary will immediately trigger placing the secondary order(s) in full.
* **For OCO**: A partial fill of the primary will immediately start the cancellation of the secondary (in practice, with OCO, usually you wait for a complete fill, but the system allows first-hit logic).
* **For OTOCO**: As soon as the primary gets its first execution, both secondary orders are placed, and linked to each other via OCO. Essentially, the protective orders go live as soon as your position starts to open, even before it's completely filled.

### Complete Fill

This mode waits until the primary order is entirely filled (fully executed) before triggering any secondaries. Under Complete Fill:

* **OTO**: The secondary order(s) will only be placed after the primary has completely filled. If the primary only partially fills and then is canceled or expires, the secondaries would never activate.
* **OCO**: The secondary order would be cancelled only when the primary is filled entirely. (A bit of an odd case for OCO since usually the primary fill isn't what's cancelling the secondary – more applicable in OTOCO context.)
* **OTOCO**: Both secondary orders are placed only once the primary is 100% filled. This means your take profit and stop won't enter the book until your entry order is fully done. Some traders prefer this to avoid having exits in the market for a position they haven't fully obtained.

### Incremental (Proportional)

This is the default on the UI and a very slick feature. In incremental mode, secondary orders are adjusted proportionally to the primary order's filled quantity:

* **For OCO**: The secondary (say a stop loss) will cancel in proportion to how much of the primary filled. For example, if your primary is filled 50%, an OCO-linked secondary might cancel 50% of its size. (OCO with incremental is less common in usage; it's more intuitive in OTOCO context.)
* **For OTO**: The secondary order will be placed in increments proportional to the fill. If your primary gets partially filled, a corresponding fraction of the secondary order is placed. For instance, primary to buy 100 BTC, secondary to sell 100 BTC (take profit). If 40 BTC of the primary fills, an order to sell 40 (or slightly less, see rounding) BTC at the take-profit price will be placed immediately. If more of the primary fills later, additional secondary amount is placed up to the total.
* **For OTOCO**: Both secondaries (stop and take profit) are placed incrementally. Using the same example, if 40% of your position is acquired, the system will place 40% of your full take-profit order and 40% of your full stop order. As your primary continues to fill, it will increase the size of those secondary orders proportionally.

**Rounding**: In incremental mode, fractional contracts or lots don't make sense, so Deribit will round the secondary order size down to the nearest whole contract that does not exceed the intended proportion. This ensures you never over-allocate secondary orders. The leftover amount (from rounding) would only be placed once the primary fully fills (if at all). Essentially, the system errs on the side of being slightly conservative in secondary size until the final fill.

Which fill condition to choose depends on your strategy. First Hit offers the fastest protection – your secondaries kick in as soon as any part of the primary is dealt. Complete Fill ensures you only place exits when you have the full position, avoiding potential scenarios where an exit could execute without the full entry (though the system prevents that anyway by linking them). Incremental strikes a balance: your protection and profit orders grow with your position, which can be useful if partial fills happen over time.

## Creating linked orders in the API

To create linked orders via API, you submit the primary order together with the configuration for any secondary orders. In the JSON-RPC API, this is done using the `linked_order_type`, `trigger_fill_condition`, and `otoco_config` parameters when placing the primary order.

* `linked_order_type` specifies the relationship between the orders
* `trigger_fill_condition` determines when the secondary orders are placed or cancelled in relation to fills on the primary order (default is "first\_hit")
* `otoco_config` is an array of objects describing the secondary orders to be created or cancelled when the primary order meets the trigger condition. Each object includes the order parameters such as instrument name, type, amount, and price.

The API will return all resulting order IDs and statuses once processed. While the web UI may restrict combinations for simplicity and safety (often allowing only one stop and one take-profit), the API provides more flexibility, enabling multiple secondary orders of different types. This flexibility should be used carefully, as incorrect configurations can lead to unintended order behaviour.

### OTOCO order example

```json theme={null}
{
  "method": "private/buy",
  "params": {
    "instrument_name": "BTC-PERPETUAL",
    "amount": 1000,
    "type": "limit",
    "price": 115000,
    "linked_order_type": "one_triggers_one_cancels_other",
    "trigger_fill_condition": "complete_fill",
    "otoco_config": [
      {
        "amount": 1000,
        "direction": "buy",
        "type": "market",
        "price": 100000,
        "trigger": "last_price"
      },
      {
        "amount": 1000,
        "direction": "sell",
        "price": 112000,
        "trigger": "mark_price"
      }
    ]
  },
  "jsonrpc": "2.0",
  "id": 3
}
```

### What this request means

This sends a primary limit buy order for BTC-PERPETUAL at \$115,000.

Once this primary order is completely filled (`trigger_fill_condition = complete_fill`), it will trigger two secondary orders:

1. A market buy order of the same size, triggered by the last\_price hitting \$100,000.
2. A limit sell order at \$112,000, triggered by the mark\_price.

The two secondary orders are linked in an OCO relationship, so if one executes, the other is automatically cancelled.

### Example response

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "order": {
      "label": "",
      "price": 115000,
      "user_id": 48595,
      "direction": "buy",
      "time_in_force": "good_til_cancelled",
      "instrument_name": "BTC-PERPETUAL",
      "api": true,
      "web": false,
      "amount": 1000,
      "order_id": "58167917688",
      "creation_timestamp": 1754907086852,
      "mmp": false,
      "order_type": "limit",
      "order_state": "open",
      "replaced": false,
      "filled_amount": 0,
      "trigger_fill_condition": "complete_fill",
      "post_only": false,
      "last_update_timestamp": 1754907086852,
      "reduce_only": false,
      "average_price": 0,
      "contracts": 100,
      "is_primary_otoco": true,
      "is_liquidation": false,
      "risk_reducing": false,
      "oto_order_ids": [
        "OTO-10838714",
        "OTO-10838715"
      ]
    },
    "trades": []
  }
}
```

### What this response confirms

* The primary buy limit order is now open at \$115,000.
* It is marked as the primary OTOCO (`is_primary_otoco = true`) with two secondary order configurations already assigned IDs (`oto_order_ids`).
* No fills yet (`filled_amount = 0`), so the secondary orders are not yet active. They will only be placed when the primary is completely filled, per the `trigger_fill_condition`.

<Note>
  The API does not babysit your linked orders beyond the conditions you've set.

  Unlike the web UI, which might prevent you from setting obviously wrong combos (like a stop loss above a take profit for a long position), the API will accept what you give it. It's possible to create a linked order setup that immediately cancels one another due to pricing overlap, or otherwise doesn't make sense. So, use this feature carefully and test your logic on the testnet if possible.
</Note>

## Other Considerations

Before we wrap up, here are a few additional best practices and facts to keep in mind:

### Rounding of position averages

When your position changes as a result of trades, Deribit calculates the new average entry price as `total_cost / total_quantity`. Internally, costs in USD are maintained with high precision (up to 8 decimal places) and amounts in BTC with up to 12 decimal places. For display purposes, however, the average price is rounded to 2 decimal places. This means the PnL shown in the UI is based on the rounded average price, while internal calculations and final settlement use the exact values. If you reconcile position costs, be aware that small rounding differences may appear between what you see in the interface and the precise calculation.

### Order and trade IDs

Each order and trade you get from the system has a unique identifier. These IDs are not globally sequential, but they are guaranteed to be unique and increasing over time. For example, your trade IDs will increase, but not every single number is used (there could be gaps, especially since trades on other accounts or instruments happen). You can rely on the fact that a later trade will have a higher ID than an earlier trade, but not that it's exactly +1. Similar for order IDs – not consecutive, but monotonic increasing in general.

### Cancel-on-disconnect (CoD)

Deribit offers an optional feature, disabled by default, called cancel-on-disconnect (CoD). When enabled, it automatically cancels your active orders if your API connection is lost. This applies to both FIX and WebSocket sessions. If you run strategies where a connection drop could leave orders in the market unmonitored, enabling CoD can help mitigate risk.

CoD must be explicitly enabled through the API or in the web interface settings. If it is not enabled and your connection drops, your orders will remain active until you cancel them manually, they are cancelled by another action, or they are fully filled or expire.

For detailed instructions on enabling and managing CoD, refer to the [Connection Management - Best Practices](/articles/connection-management-best-practices) article or the API documentation.

### Rate limits

While not directly covered in the section above, remember Deribit has API rate limits. Bursty behavior like sending many orders or cancellations rapidly is subject to limits. Hitting a rate limit will cause your session to disconnect and could negate your latency gains. Best practice is to stay within documented limits or contact Deribit if you need higher thresholds for institutional trading.

### Test in the Testnet environment

If you are deploying complex order logic (like OTOCO or high-frequency strategies), always test on `test.deribit.com` first. The API is virtually identical, and you can simulate scenarios (including partial fills, cancels, etc.) without risking real funds. This can also confirm that your understanding of the API calls (especially for linked orders) is correct. Please refer to Testnet related articles for more details.

By incorporating the strategies and considerations discussed above, you can significantly improve your order management on Deribit. From reducing latency in order submission to utilizing advanced order types for automation, these best practices will help ensure your trading is efficient, robust, and aligned with how the Deribit platform works internally.
