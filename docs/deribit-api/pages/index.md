> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Welcome to Deribit API

> Deribit is a leading cryptocurrency derivatives exchange offering futures, perpetuals, and options trading. This documentation provides everything you need to integrate with our API and build powerful trading applications.

<Info>
  Two versions of the API documentation are available. You can switch between them using the version selector button at the top of the page. Changes in the upcoming version will be available in the production version after the next release. For release notes and information about upcoming releases, visit the [Releases section](https://support.deribit.com/hc/en-us/sections/25944734788637-Releases).
</Info>

## API Interfaces

Deribit provides three different interfaces to access the API:

<CardGroup cols={3}>
  <Card title="JSON-RPC over WebSocket" icon="plug" href="/articles/json-rpc-overview#websocket-preferred">
    Real-time, bidirectional communication. Recommended for most use cases.
  </Card>

  <Card title="JSON-RPC over HTTP" icon="globe" href="/articles/json-rpc-overview#http-rest">
    Simple REST-like interface for HTTP requests.
  </Card>

  <Card title="FIX API" icon="network-wired" href="/fix-api/production/overview">
    Financial Information eXchange protocol for institutional trading.
  </Card>
</CardGroup>

## Get Started

<Card title="Quickstart Guide" icon="rocket" href="/articles/deribit-quickstart" horizontal>
  Get up and running in minutes with our step-by-step quickstart guide. Make your first API call and start building.
</Card>

## Core Concepts

<Columns cols={2}>
  <Card title="Authentication" icon="key" href="/articles/creating-api-key">
    Learn how to create and manage API keys, and authenticate your requests.
  </Card>

  <Card title="Rate Limits" icon="gauge" href="/articles/rate-limits">
    Understand rate limits, credit system, and how to optimize API usage.
  </Card>

  <Card title="Access Scopes" icon="shield" href="/articles/access-scope">
    Learn about API permissions and access scopes for controlling what operations your API keys can perform.
  </Card>

  <Card title="Notifications" icon="bell" href="/articles/notifications">
    Subscribe to real-time market data and account updates.
  </Card>

  <Card title="Error Codes" icon="triangle-exclamation" href="/articles/errors">
    Reference guide for all API error codes and error handling.
  </Card>

  <Card title="API Console" icon="terminal" href="https://test.deribit.com/api_console/">
    Interactive API testing tool for exploring and testing API methods.
  </Card>
</Columns>

## Environments

<Info>
  Deribit provides separate test and production environments. All examples in this documentation use the test environment (`test.deribit.com`). Test and production require separate accounts and API keys.
</Info>

<CardGroup cols={2}>
  <Card title="Test Environment" icon="flask" href="https://test.deribit.com/dashboard">
    **Purpose:** Development and testing

    **HTTP Endpoint:** `https://test.deribit.com/api/v2`

    **WebSocket Endpoint:** `wss://test.deribit.com/ws/api/v2`

    **Links:**

    * [Platform](https://test.deribit.com)
    * [API Console](https://test.deribit.com/api_console/)
    * [API Management](https://test.deribit.com/account/BTC/api)
  </Card>

  <Card title="Production Environment" icon="server" href="https://www.deribit.com/">
    **Purpose:** Live trading

    **HTTP Endpoint:** `https://www.deribit.com/api/v2`

    **WebSocket Endpoint:** `wss://www.deribit.com/ws/api/v2`

    **Links:**

    * [Platform](https://www.deribit.com)
    * [API Console](https://www.deribit.com/api_console/)
    * [API Management](https://www.deribit.com/account/BTC/api)
  </Card>
</CardGroup>

## Need Help?

<CardGroup cols={2}>
  <Card title="Support Center" icon="life-ring" href="https://support.deribit.com">
    Browse help articles and documentation.
  </Card>

  <Card title="Contact Us" icon="envelope" href="https://insights.deribit.com/contact-us/">
    Get technical support, API assistance, or report bugs. Available via Telegram, email, or support portal.
  </Card>
</CardGroup>
