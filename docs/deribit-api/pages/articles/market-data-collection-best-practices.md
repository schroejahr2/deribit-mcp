> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/market-data-collection-best-practices",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Market Data Collection

> Efficient market data consumption is critical for algorithmic trading on Deribit.

This article outlines how to get the most timely and reliable market data from Deribit's API, while minimizing latency and system load. We cover Deribit's market data architecture, choosing the right interface (WebSocket, FIX, or Multicast), raw vs. aggregated data streams, optimal subscription patterns, and connection management. Following these best practices will help ensure you receive price and order book updates as quickly as possible without overloading your systems or Deribit's.

## Market Data Architecture and Latency

Deribit's trading platform distributes market data through a multi-node, parallelized system. Each instrument (order book) produces its own stream of events (orders, trades, etc.) independently, which are then distributed across multiple processing nodes for formatting and forwarding to clients. This means the load is shared and market data is generated in parallel, for example, BTC and ETH products are handled on separate threads/cores. As a user, you won't usually see this complexity (and there's no indicator of which node sent a given update), but it underpins Deribit's ability to handle high throughput.

**Event Ordering**: Deribit guarantees that within each instrument's feed, events are delivered in the exact order they occurred. Sequence numbers (like `change_id` for order book updates) allow your client to verify continuity. So, you can trust that price updates for a given instrument won't arrive out of sequence. (Cross-instrument timing is inherently asynchronous, e.g. BTC updates may interleave with ETH updates, but each instrument's chronology is preserved.)

<Info>
  If you want to know more details regarding order management, please refer to [Order Management - Best Practices](/articles/order-management-best-practices).
</Info>

<Tabs>
  <Tab title="WebSocket">
    For receiving realtime data, WebSocket and FIX connections are equally fast in practice. Both interfaces tap into the same event streams and deliver updates as soon as they're processed. In other words, there's no inherent latency advantage to using FIX over WebSocket, or vice versa, for market data as they both provide millisecond-level realtime updates. Use whichever suits your infrastructure (WebSocket's JSON is convenient and feature-rich, while FIX uses binary feeds compliant with financial industry norms), knowing that speed will be comparable.

    <Card title="WebSocket Guide" icon="plug" href="/articles/json-rpc-overview">
      Learn about WebSocket connections and subscriptions
    </Card>
  </Tab>

  <Tab title="FIX">
    FIX connections provide the same latency as WebSocket for market data. FIX uses binary feeds compliant with financial industry norms, making it suitable for institutional trading systems.

    <Card title="FIX API" icon="network-wired" href="/fix-api/production/overview">
      Learn about FIX API for institutional trading
    </Card>
  </Tab>

  <Tab title="Multicast (LD4)">
    For the lowest possible latency, Deribit offers a multicast market data feed for clients in close network proximity. This is available to co-located clients (and via special AWS arrangements) as a UDP stream using SBE (Simple Binary Encoding). Deribit's multicast feed provides a high-performance broadcast of public market data with minimal overhead and latency. Migrating heavy data consumers to multicast can significantly reduce latency (no JSON parsing, no per-connection delivery delays) and also relieve load on Deribit's API nodes. This is the fastest way to receive Deribit data – but it requires more complex integration (binary message decoding) and network setup (joining multicast groups, typically in LD4 or supported AWS regions).
  </Tab>

  <Tab title="AWS Multicast">
    Deribit enables access to its multicast feed for AWS-hosted clients. This solution packages the multicast data into TCP streams and leverages AWS's ability to share multicast across accounts. Clients in AWS (London eu-west-2 or Tokyo ap-northeast-1) can subscribe to Deribit's low-latency feed and receive the same market data simultaneously as colocation users, with very similar latency to a direct LD4 connection. In other words, all subscribers in the AWS relay get the updates in parallel, eliminating any edge a "faster" connection might have, and bringing cloud users nearly on par with physical co-location in terms of tick-to-trade speed.
  </Tab>
</Tabs>

<Info>
  If you want to know more details regarding Multicast and AWS setup please refer to these articles:

  * [Multicast Developer Guide](https://support.deribit.com/hc/en-us/sections/28388652682653-Multicast)
  * [Deribit AWS Multicast Service Instruction](https://support.deribit.com/hc/en-us/articles/25944617728285-Deribit-AWS-Multicast-Service-Instruction)
</Info>

<Tip>
  If ultra-low latency is not critical in your strategy, Deribit actually encourages you to use the higher-level aggregated feeds. Using these reduces the load on core systems, benefitting overall exchange performance. In summary: use the rawest, fastest feeds only if you truly need them; otherwise, a slightly throttled feed or the shared event node is "good enough" and friendlier to both client and server.
</Tip>

## Raw vs. Aggregated Data Streams

Deribit provides market data channels in two flavors: "raw" feeds vs. aggregated (batched) feeds.

<Tabs>
  <Tab title="Raw Channels">
    Raw channels deliver every single update as an individual message, with no batching. For example, subscribing to [`book.<instrument>.raw`](/subscriptions/orderbook/bookinstrument_nameinterval) gives you an order book change notification for every order insertion, update, or deletion in that book. This yields the most granular, up-to-the-moment view of the market. If you want the absolutely earliest signal of a book change or trade, use raw channels. However, raw feeds generate high message volumes, especially in active instruments, which can tax your network and client if not handled efficiently.

    <Note>
      Raw public feeds require an authenticated connection, as a safeguard against abuse.
    </Note>
  </Tab>

  <Tab title="Aggregated Channels">
    Aggregated channels deliver updates in batches or at a fixed interval. For instance, you might subscribe to [`book.BTC-PERPETUAL.100ms`](/subscriptions/orderbook/bookinstrument_nameinterval) (updates grouped by 100ms) or `agg2` aggregation type. These feeds consolidate multiple updates into one message or snapshot at a set frequency. The result is lower message frequency, easier for clients to process, at the cost of a few milliseconds of delay. If you don't require tick-by-tick detail, aggregated feeds are recommended to reduce load.

    <Note>
      The `agg2` aggregation channel groups updates at roughly 1 second intervals.
    </Note>
  </Tab>
</Tabs>

In general, both raw and aggregated channels are processed with the same priority on Deribit's side. Subscribing to an aggregated feed doesn't mean Deribit will send it any slower – the data pipeline is the same, just with batching. Where you will notice a difference is in throughput: a raw feed might send dozens of messages in a volatile second, whereas a 100ms feed might send 1–2 messages in that same second (each possibly containing multiple changes). Fewer messages means less client-side JSON parsing and less chance of your inbound queue backing up.

<Note>
  **Raw Feed Coalescing**: Deribit strives to never aggregate the raw feed… but there are rare cases during extreme load where even "raw" subscriptions can arrive slightly aggregated. This is due to multiple internal processes handling notifications; if certain nodes or CPU cores are under heavy strain, some events might get combined before reaching you. This scenario is unlikely in normal operation, but be aware that during peak bursts (e.g. huge volatility spikes) you might occasionally see a raw order book change that actually represents two or three changes at once. Your client logic should handle this gracefully (e.g. by applying the batched changes in order) – it's effectively the same outcome, just not one update per message in that moment.
</Note>

## Subscription Strategies and Filters

Deribit's API allows a flexible subscription to many channels. Here are practices to optimize what you subscribe to and how:

### Subscribe only to what you need (Narrow vs. Wide subscriptions)

You can subscribe at different scopes. For example, [`trades.BTC-PERPETUAL.raw`](/subscriptions/trades/tradesinstrument_nameinterval) gives only trades on that instrument, whereas [`trades.future.BTC.raw`](/subscriptions/trades/tradeskindcurrencyinterval) would deliver all BTC futures trades across every expiration. While both will ultimately deliver the same information if you aggregate it, the wide subscription (`trades.future.BTC.raw`) will flood you with a lot of data if you only care about a few specific futures. In general, specificity is better for performance – subscribing to a narrower channel means less data sent over your connection, less JSON to parse, and less filtering for you to do on the client side. Wide subscriptions (using broad channel patterns like all options or all instruments of a currency) are convenient, but they include many events you might not be interested in, which can overwhelm your client or network. If you know you only need certain instruments, subscribe to them individually.

The only downside of narrow subscriptions is that you must keep track of instruments dynamically. For example, if you want to track all options for BTC, subscribing to each one individually is efficient, but you'll need to catch when new option strikes are listed and subscribe to those too (Deribit lists new expiries/strikes regularly). This is manageable using the instrument notifications (described below), but requires a bit more logic. By contrast, [`trades.option.BTC.raw`](/subscriptions/trades/tradeskindcurrencyinterval) will automatically cover new options as they appear – at the cost of a lot of unwanted noise. Decide based on your use-case: if missing a new instrument for a few seconds matters, you might use one broad subscription; otherwise, it's usually worth the upkeep to stay narrow.

### Instrument Lifecycle Feed

To manage a dynamic set of subscriptions (as new instruments come and old ones expire), take advantage of the instrument lifecycle feed. Deribit provides a channel [`instrument.state.{kind}.{currency}`](/subscriptions/market-data/instrumentstatekindcurrency) which notifies you of state changes for instruments, including when new instruments become available for trading, when they enter different lifecycle stages (such as settlement or delivery), and when they are archived after expiry. For example, you can subscribe to `instrument.state.option.BTC` to get events whenever a BTC option's state changes. Many institutional users subscribe to `instrument.state.any.any` (all instruments) to drive their subscription management logic. This is far better than polling [`/public/get_instruments`](/api-reference/market-data/public-get_instruments) repeatedly. In fact, Deribit explicitly requests clients to use this channel instead of frequent instrument queries, which put unnecessary load on the system. By handling these notifications, you can automatically subscribe to new instruments of interest as soon as they appear (when their state becomes `open`), and drop subscriptions for instruments that reach terminal states like `delivered` or `archivized`.

The `state` field represents the current lifecycle stage of an instrument's order book and defines what actions are permitted at each stage. Key states include:

* `open` - Active trading state where orders, edits, and cancellations are accepted
* `locked` - New orders and edits are not accepted, but cancellations are allowed
* `settlement` - During settlement or delivery processing; no new orders, edits, or cancellations
* `delivered` - Final state after delivery completion; all open orders are canceled
* `inactive` - Book is not tradable; all open orders are canceled
* `halted` - Error condition state; settlement is not possible
* `archivized` - Final archival state after the instrument is moved to expired instruments

<Tip>
  You can also use the [`public/get_expirations`](/api-reference/market-data/public-get_expirations) method to retrieve the current list of valid expirations for a given currency and instrument type, which is helpful for initializing subscriptions or verifying expiry dates when new instruments appear.
</Tip>

### Avoid excessive REST polling

On a related note, prefer the real-time subscription channels to any kind of constant polling via REST. For instance, if you want live trades or quotes, do not call [`/public/get_last_trades_by_instrument`](/api-reference/market-data/public-get_last_trades_by_instrument) or [`/public/get_order_book`](/api-reference/market-data/public-get_order_book) in a loop – use the WebSocket feed to push updates to you. Polling not only introduces latency (you're always behind by your polling interval), but it also consumes your rate limits and adds load to the API servers. Reserve REST for infrequent queries (snapshots, historical data, or occasional state syncs). The streaming API is designed to push timely data to you – use it for anything time-sensitive.

### Batch your subscription requests

Deribit allows you to subscribe to multiple channels in a single API call, which is much more efficient than subscribing one by one. When your WebSocket connection is open, prepare a single [`public/subscribe`](/api-reference/subscription-management/public-subscribe) call with an array of all channels you want. The system can handle up to 500 channels in one subscription message, which should be more than sufficient in practice. Subscribing in bulk reduces the overhead (latency and load) of sending many small requests and ensures you start receiving all data at once. For example, instead of doing 100 separate `public/subscribe` calls for 100 instruments, do one call with a "channels" list of those 100. The snippet below illustrates a single request subscribing to four channels at once:

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 42,
  "method": "public/subscribe",
  "params": {
    "channels": [
      "ticker.BTC-PERPETUAL.raw",
      "ticker.ETH-PERPETUAL.raw",
      "book.BTC-PERPETUAL.raw",
      "book.ETH-PERPETUAL.raw"
    ]
  }
}
```

<Note>
  Channel references: [`ticker.*`](/subscriptions/market-data/tickerinstrument_nameinterval), [`book.*`](/subscriptions/orderbook/bookinstrument_nameinterval)
</Note>

The response will confirm all channels subscribed. Using one message means minimal round-trip delay and a synchronized start for your feeds. (If you have extremely many channels, you can break them into batches – e.g. 2 messages of 500 each – but avoid spamming the API with hundreds of separate subscribe calls.)

## Connection Management and Performance

### Use separate connections for trading vs. market data

Perhaps the most important practice for performance is to isolate your order traffic from your data feed. Deribit allows multiple WebSocket (or FIX) connections, and you should take advantage of that. Run one connection dedicated to market data subscriptions, and another (or several) dedicated to order entry and other private actions. The reason is that if you combine them, a flood of incoming data can congest the connection and delay your outgoing order commands or their acknowledgments. Even though Deribit's infrastructure processes public (data) and private (order) messages in separate threads, they still share the same TCP pipeline on one socket. A heavy stream of JSON quotes could fill up the TCP receive buffer or your client's processing loop, meaning your next order cancel might sit behind a pile of incoming messages. By splitting data and trading onto different sockets, you ensure that a surge of market events does not block your critical trading messages.

<Tip>
  For further guidance on connection setup, see the [Connection Management - Best Practices](/articles/connection-management-best-practices) article.
</Tip>

<Tip>
  Deribit's FIX API offers a `ConnectionOnlyExecutionReports` flag (tag 9010 on Logon) that can further isolate order updates if you use multiple FIX connections for a single account. Setting this to "Y" on a FIX session means that session will only receive execution reports for orders it placed, not for orders from your other sessions. This can be useful if you have two or more active trading algorithms using separate FIX connections.
</Tip>

### Monitor your connection health and latency

With high-throughput data streams, it's important to watch for any signs of lag. Deribit includes sequence numbers (`change_id` and `prev_change_id` in order book updates, incremental `trade_id` or timestamps for trades, etc.) – use these to detect if you've missed a message (e.g. a gap in sequence). If you suspect you missed data (perhaps due to a momentary network issue), you can call REST endpoints like [`/public/get_order_book`](/api-reference/market-data/public-get_order_book) to resync. It's rare, but maintaining a resiliency mechanism is a best practice for any real-time feed.

### Optimize your network location

Deribit's primary servers are in London (Equinix LD4). If low latency is crucial, host your client as close to London as possible or even consider co-location services. Internet latency and routing can vary – many serious traders use cross-connects. Even the \~1ms added by a load balancer or the 50ms cross-continent delay can matter in high-frequency trading. If you're on the other side of the world and cannot relocate, using the AWS Multicast (in Tokyo or London regions) might be the next best thing to get a level playing field.

## Summary

By using the guidelines above, you can build a market data collection system that is both fast and robust:

* **Choose the right feed** – Use WebSockets or FIX for real-time data (they have similar performance), and if you need ultra-low latency, explore Deribit's multicast feed or AWS Multicast. Otherwise, the default feeds are sufficient and easier to work with.

* **Raw vs Aggregated** – Subscribe to raw book/trade feeds only if you truly need every tick. Otherwise, opt for 100ms or aggregated updates to reduce noise. Deribit's system will thank you for using aggregated channels when possible.

* **Minimize data volume** – Filter your subscriptions to only what you need. Avoid wildcards that dump unnecessary data on you. Use multiple targeted channels rather than one huge firehose.

* **Subscribe smartly** – Batch subscriptions in one request (up to 500 channels) for efficiency. Utilize the [`instrument.state`](/subscriptions/market-data/instrumentstatekindcurrency) feed to catch new listings and expirations so you can adapt your subscriptions in real-time.

* **Isolate connections** – Always use separate connections for market data vs. order execution. This isolation prevents data surges from delaying your trading. If using multiple connections on FIX, consider the 9010 tag to avoid duplicate reports.

By following these best practices, you'll ensure you're getting the fastest possible market updates from Deribit in a reliable manner, positioning you to react quickly in the market while maintaining a stable system. Happy trading!
