> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/deribit-quickstart",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Quickstart Guide

> Welcome to the Deribit API! This guide will help you make your first API call in minutes.

Deribit provides three different interfaces to access the API:

* **JSON-RPC over WebSocket** (recommended) - Real-time, bidirectional communication
* **JSON-RPC over HTTP** - Simple REST-like interface
* **FIX API** - Financial Information eXchange protocol for institutional trading

<Info>
  All examples in this documentation use the **test environment** (`test.deribit.com`). To use production, change the URLs to `www.deribit.com`. Test and production environments are separate and require different accounts and API keys.
</Info>

<Steps>
  <Step title="Get API Credentials">
    <ol>
      <li>Log in to your Deribit account at [www.deribit.com](https://www.deribit.com) or [test.deribit.com](https://test.deribit.com) for testing</li>
      <li>Navigate to **Account** → **API**</li>
      <li>Create a new API key with appropriate permissions</li>
      <li>Save your **Client ID** and **Client Secret** securely</li>
    </ol>

    <Warning>
      Never share your API credentials or commit them to version control. The client secret is only shown once and cannot be retrieved later.
    </Warning>

    <CardGroup cols={2}>
      <Card title="Creating API Keys" icon="key" href="/articles/creating-api-key">
        Step-by-step guide to creating API keys
      </Card>

      <Card title="Asymmetric API Keys" icon="shield" href="/articles/asymmetric-api-keys">
        Using Ed25519 or RSA key pairs for enhanced security
      </Card>
    </CardGroup>
  </Step>

  <Step title="Choose Your Interface">
    <Tabs>
      <Tab title="HTTP (Simplest)">
        <Badge>Best for: Simple scripts, one-off requests, testing</Badge>

        ```bash theme={null}
        # Get market data (no authentication required)
        curl -X GET "https://test.deribit.com/api/v2/public/get_instruments?currency=BTC&kind=future"
        ```
      </Tab>

      <Tab title="WebSocket (Recommended)">
        <Badge>Best for: Real-time data, subscriptions, trading bots</Badge>

        ```javascript theme={null}
        const WebSocket = require('ws');
        const ws = new WebSocket('wss://test.deribit.com/ws/api/v2');

        ws.on('open', function open() {
          // Subscribe to order book updates
          ws.send(JSON.stringify({
            "jsonrpc": "2.0",
            "method": "public/subscribe",
            "params": {
              "channels": ["book.BTC-PERPETUAL.100ms"]
            },
            "id": 1
          }));
        });

        ws.on('message', function incoming(data) {
          console.log(JSON.parse(data));
        });
        ```
      </Tab>

      <Tab title="FIX API">
        <Badge>Best for: Institutional trading, high-frequency trading</Badge>

        See the [FIX API documentation](/fix-api/production/overview) for details.
      </Tab>
    </Tabs>
  </Step>

  <Step title="Authenticate">
    For private methods, you need to authenticate. Deribit supports multiple authentication methods:

    <ul>
      <li><strong>Client Credentials</strong> - Standard OAuth 2.0 flow</li>
      <li><strong>Client Signature</strong> - User generated signature</li>
      <li><strong>Refresh Token</strong> - Token renewal</li>
    </ul>

    <Tabs>
      <Tab title="HTTP Authentication">
        ```bash theme={null}
        # Get access token using Client Credentials
        curl -X GET "https://test.deribit.com/api/v2/public/auth" \
          -d "grant_type=client_credentials" \
          -d "client_id=YOUR_CLIENT_ID" \
          -d "client_secret=YOUR_CLIENT_SECRET"
        ```

        Response:

        ```json theme={null}
        {
          "jsonrpc": "2.0",
          "result": {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "expires_in": 31536000,
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "scope": "account:read trade:read",
            "token_type": "bearer"
          }
        }
        ```
      </Tab>

      <Tab title="WebSocket Authentication">
        ```javascript theme={null}
        const WebSocket = require('ws');
        const ws = new WebSocket('wss://test.deribit.com/ws/api/v2');

        ws.on('open', function open() {
          // Authenticate
          ws.send(JSON.stringify({
            "jsonrpc": "2.0",
            "method": "public/auth",
            "params": {
              "grant_type": "client_credentials",
              "client_id": "YOUR_CLIENT_ID",
              "client_secret": "YOUR_CLIENT_SECRET"
            },
            "id": 1
          }));
        });

        ws.on('message', function incoming(data) {
          const response = JSON.parse(data);
          if (response.result && response.result.access_token) {
            console.log('Authenticated! Access token:', response.result.access_token);
            // Now you can make private method calls
          }
        });
        ```
      </Tab>
    </Tabs>

    <Card title="Access Scopes" icon="user-shield" href="/articles/access-scope">
      Learn more about API permissions and access scopes
    </Card>
  </Step>

  <Step title="Make Your First Requests">
    <Tabs>
      <Tab title="Public Data (No Auth)">
        **Get Market Data**

        ```bash theme={null}
        # Get all BTC futures
        curl -X GET "https://test.deribit.com/api/v2/public/get_instruments?currency=BTC&kind=future"

        # Get ticker for BTC-PERPETUAL
        curl -X GET "https://test.deribit.com/api/v2/public/ticker?instrument_name=BTC-PERPETUAL"

        # Get order book
        curl -X GET "https://test.deribit.com/api/v2/public/get_order_book?instrument_name=BTC-PERPETUAL&depth=5"
        ```
      </Tab>

      <Tab title="Private Data (Auth Required)">
        **Get Account Information**

        ```bash theme={null}
        # Get account summary
        curl -X GET "https://test.deribit.com/api/v2/private/get_account_summary?currency=BTC" \
          -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

        # Get open orders
        curl -X GET "https://test.deribit.com/api/v2/private/get_open_orders?currency=BTC" \
          -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
        ```
      </Tab>

      <Tab title="WebSocket Subscriptions">
        **Subscribe to Real-Time Data**

        ```javascript theme={null}
        const WebSocket = require('ws');
        const ws = new WebSocket('wss://test.deribit.com/ws/api/v2');

        ws.on('open', function open() {
          // Subscribe to multiple channels
          ws.send(JSON.stringify({
            "jsonrpc": "2.0",
            "method": "public/subscribe",
            "params": {
              "channels": [
                "book.BTC-PERPETUAL.100ms",
                "ticker.BTC-PERPETUAL.100ms",
                "trades.BTC-PERPETUAL.100ms"
              ]
            },
            "id": 1
          }));
        });

        ws.on('message', function incoming(data) {
          const message = JSON.parse(data);
          if (message.method === 'subscription') {
            console.log('Update:', message.params.channel, message.params.data);
          }
        });
        ```
      </Tab>
    </Tabs>
  </Step>

  <Step title="Place a Test Order (Testnet Only)">
    <Warning>
      Only use test.deribit.com for testing. Never test with real funds on production.
    </Warning>

    <Tabs>
      <Tab title="HTTP">
        ```bash theme={null}
        # Place a limit buy order (testnet)
        curl -X GET "https://test.deribit.com/api/v2/private/buy" \
          -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
          -d "instrument_name=BTC-PERPETUAL" \
          -d "amount=10" \
          -d "type=limit" \
          -d "price=50000"
        ```
      </Tab>

      <Tab title="WebSocket">
        ```javascript theme={null}
        ws.send(JSON.stringify({
          "jsonrpc": "2.0",
          "method": "private/buy",
          "params": {
            "instrument_name": "BTC-PERPETUAL",
            "amount": 10,
            "type": "limit",
            "price": 50000,
            "access_token": "YOUR_ACCESS_TOKEN"
          },
          "id": 2
        }));
        ```
      </Tab>
    </Tabs>
  </Step>
</Steps>
