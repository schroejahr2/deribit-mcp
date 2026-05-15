"""Phase 18.D smoke — verifies that Deribit OTOCO accepts a stop-* primary leg.

Runs against whichever Deribit endpoint `settings.deribit_test_mode` resolves
to. Reads credentials from the standard env via `Settings.effective_api_*`
so the script naturally inherits the same testnet/mainnet flip the server uses.

Exits non-zero on the first failure so it is safe to wire into smoke CI later.

Usage:
    DERIBIT_TEST_MODE=true python -m scripts.smoke_bracket_18d
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from typing import Any, Optional

from src.config import settings
from src.deribit_rest import DeribitRestClient

INSTRUMENT = "BTC-PERPETUAL"
AMOUNT = 10  # inverse contracts → $10 notional, well under any reasonable cap


def log(stage: str, payload: Any) -> None:
    print(f"[{stage}]", json.dumps(payload, default=str, indent=2)[:2000])


async def _safe_cancel(rest: DeribitRestClient, order_id: Optional[str]) -> None:
    if not order_id:
        return
    try:
        await rest.cancel_order(order_id)
        log("cancel", {"order_id": order_id, "status": "ok"})
    except Exception as exc:
        log("cancel", {"order_id": order_id, "status": "failed", "error": str(exc)})


async def _hydrate_children(
    rest: DeribitRestClient, decision_label: str
) -> dict[str, Optional[str]]:
    """Best-effort lookup of OTOCO child SL/TP via trigger_order_history."""
    try:
        history = await rest.get_trigger_order_history(currency="BTC", count=20)
    except Exception as exc:
        return {"sl": None, "tp": None, "error": str(exc)}
    children: dict[str, Optional[str]] = {"sl": None, "tp": None}
    for entry in history.get("entries", []) or []:
        if entry.get("label") != decision_label:
            continue
        order_type = entry.get("order_type")
        if order_type == "stop_market" and not children["sl"]:
            children["sl"] = entry.get("trigger_order_id")
        elif order_type == "take_market" and not children["tp"]:
            children["tp"] = entry.get("trigger_order_id")
    return children


async def main() -> int:
    print(f"=== smoke 18.D | test_mode={settings.deribit_test_mode} ===")
    print(f"REST endpoint: {settings.deribit_rest_url}")
    if not settings.effective_api_key or not settings.effective_api_secret:
        print("FATAL: no effective credentials configured", file=sys.stderr)
        return 2

    rest = DeribitRestClient()
    await rest.connect()
    try:
        ticker = await rest.get_ticker(INSTRUMENT)
        mark = float(ticker.get("mark_price") or ticker.get("last_price"))
        meta = await rest.get_instrument(INSTRUMENT)
        tick = float(meta.get("tick_size") or 0.5)
        log("mark", {"instrument": INSTRUMENT, "mark": mark, "tick_size": tick})

        def snap(price: float) -> float:
            return round(round(price / tick) * tick, 8)

        # ----- 18.D.1: stop_market entry, well above current mark -----
        trig = snap(mark * 1.05)
        sl_t = snap(trig * 0.99)
        tp_t = snap(trig * 1.02)
        label = f"smoke-18D1-{uuid.uuid4().hex[:8]}"
        otoco_config = [
            {
                "amount": AMOUNT,
                "direction": "sell",
                "type": "stop_market",
                "trigger": "mark_price",
                "trigger_price": sl_t,
                "reduce_only": True,
                "label": label,
            },
            {
                "amount": AMOUNT,
                "direction": "sell",
                "type": "take_market",
                "trigger": "mark_price",
                "trigger_price": tp_t,
                "reduce_only": True,
                "label": label,
            },
        ]

        print()
        print(f"--- 18.D.1: stop_market entry @ {trig} (mark={mark}) ---")
        entry_order_id: Optional[str] = None
        try:
            resp = await rest.place_otoco(
                side="buy",
                instrument=INSTRUMENT,
                amount=AMOUNT,
                entry_type="stop_market",
                entry_price=None,
                label=label,
                entry_post_only=False,
                trigger_fill_condition="incremental",
                otoco_config=otoco_config,
                entry_trigger="last_price",
                entry_trigger_price=trig,
            )
            log("place_otoco.response", resp)
            order = resp.get("order") if isinstance(resp, dict) else None
            if isinstance(order, dict):
                entry_order_id = order.get("order_id")
                log(
                    "entry.summary",
                    {
                        "order_id": entry_order_id,
                        "order_type": order.get("order_type"),
                        "order_state": order.get("order_state"),
                        "trigger": order.get("trigger"),
                        "trigger_price": order.get("trigger_price"),
                        "oto_order_ids": order.get("oto_order_ids"),
                    },
                )
        except Exception as exc:
            log("place_otoco.error", {"error": str(exc)})
            print()
            print(
                "RESULT: Deribit REJECTED OTOCO with a stop_* primary leg. "
                "Switch place_otoco to the OTO-fallback path (sequential entry "
                "trigger + attached children after fill)."
            )
            return 1

        # Hydrate children (best-effort)
        await asyncio.sleep(1.0)  # trigger_order_history is async on Deribit
        children = await _hydrate_children(rest, label)
        log("children.hydrated", children)

        # Inspect entry state to confirm trigger params landed.
        if entry_order_id:
            try:
                state = await rest.get_order_state(entry_order_id)
                log(
                    "entry.state",
                    {
                        "order_id": state.get("order_id"),
                        "order_type": state.get("order_type"),
                        "order_state": state.get("order_state"),
                        "trigger": state.get("trigger"),
                        "trigger_price": state.get("trigger_price"),
                    },
                )
            except Exception as exc:
                log("entry.state.error", {"error": str(exc)})

        print()
        print("RESULT 18.D.1: Deribit ACCEPTED OTOCO with a stop_market primary leg.")

        # ----- cleanup .1 -----
        print()
        print("--- 18.D.1 cleanup ---")
        await _safe_cancel(rest, entry_order_id)
        for cid in (children.get("sl"), children.get("tp")):
            await _safe_cancel(rest, cid)

        # ----- 18.D.3: stop_limit variant -----
        # (18.D.2 = already-past trigger reject is client-side logic in
        # `_place_bracket_impl`; covered by tests/test_server_helpers.py
        # cases `test_place_bracket_rejects_already_triggered_{buy,sell}`.
        # No additional value from a live Deribit round-trip.)
        trig3 = snap(mark * 1.05)
        limit3 = snap(trig3 * 1.001)
        sl_t3 = snap(trig3 * 0.99)
        tp_t3 = snap(trig3 * 1.02)
        label3 = f"smoke-18D3-{uuid.uuid4().hex[:8]}"
        otoco_config3 = [
            {
                "amount": AMOUNT,
                "direction": "sell",
                "type": "stop_market",
                "trigger": "mark_price",
                "trigger_price": sl_t3,
                "reduce_only": True,
                "label": label3,
            },
            {
                "amount": AMOUNT,
                "direction": "sell",
                "type": "take_market",
                "trigger": "mark_price",
                "trigger_price": tp_t3,
                "reduce_only": True,
                "label": label3,
            },
        ]

        print()
        print(f"--- 18.D.3: stop_limit entry trig={trig3} limit={limit3} " f"(mark={mark}) ---")
        entry_order_id3: Optional[str] = None
        try:
            resp3 = await rest.place_otoco(
                side="buy",
                instrument=INSTRUMENT,
                amount=AMOUNT,
                entry_type="stop_limit",
                entry_price=limit3,
                label=label3,
                entry_post_only=False,
                trigger_fill_condition="incremental",
                otoco_config=otoco_config3,
                entry_trigger="last_price",
                entry_trigger_price=trig3,
            )
            log("place_otoco.response.18D3", resp3)
            order3 = resp3.get("order") if isinstance(resp3, dict) else None
            if isinstance(order3, dict):
                entry_order_id3 = order3.get("order_id")
                log(
                    "entry.summary.18D3",
                    {
                        "order_id": entry_order_id3,
                        "order_type": order3.get("order_type"),
                        "order_state": order3.get("order_state"),
                        "trigger": order3.get("trigger"),
                        "trigger_price": order3.get("trigger_price"),
                        "price": order3.get("price"),
                    },
                )
            print()
            print("RESULT 18.D.3: Deribit ACCEPTED OTOCO with a stop_limit primary leg.")
        except Exception as exc:
            log("place_otoco.error.18D3", {"error": str(exc)})
            print()
            print("RESULT 18.D.3: Deribit REJECTED stop_limit primary leg.")
            await _safe_cancel(rest, entry_order_id3)
            return 1

        # cleanup .3
        print()
        print("--- 18.D.3 cleanup ---")
        await _safe_cancel(rest, entry_order_id3)
        await asyncio.sleep(0.5)
        children3 = await _hydrate_children(rest, label3)
        for cid in (children3.get("sl"), children3.get("tp")):
            await _safe_cancel(rest, cid)

        return 0
    finally:
        await rest.disconnect()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
