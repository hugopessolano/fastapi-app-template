import argparse
import os
import sys
import time
import uuid
from pathlib import Path
from subprocess import Popen

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run E2E flow for orders with embedded items.")
    parser.add_argument("--port", type=int, default=8010)
    parser.add_argument("--base-url", default="")
    parser.add_argument("--db", default="app/e2e.db")
    parser.add_argument("--no-server", action="store_true")
    parser.add_argument("--keep-db", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=60)
    return parser.parse_args()


def build_database_url(path: str) -> str:
    if path.startswith("sqlite://"):
        return path
    return f"sqlite:///./{path}"


def start_server(port: int, database_url: str) -> Popen:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    env["ENABLE_SEED_DATA"] = "true"
    env["SEED_CHECK_EXISTING_USERS"] = "false"
    env["AUTO_BUILD_PERMISSIONS"] = "true"
    env["AUTH_MODE"] = "built_in"
    env["TENANTS_ENABLED"] = "true"
    return Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)],
        env=env,
    )


def stop_server(proc: Popen | None) -> None:
    if proc is None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()


def wait_for_login(session: requests.Session, base_url: str, timeout_seconds: int) -> str:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = session.post(
                f"{base_url}/v1/auth/login",
                data={
                    "username": "admin@admin.com",
                    "password": "admin",
                    "grant_type": "password",
                },
                timeout=5,
            )
            if response.status_code == 200:
                token = response.json().get("access_token")
                if token:
                    return token
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError("Login failed within timeout.")


def run_flow(base_url: str) -> None:
    session = requests.Session()
    token = wait_for_login(session, base_url, timeout_seconds=60)
    headers = {"Authorization": f"Bearer {token}"}
    suffix = uuid.uuid4().hex[:8]

    customer_resp = session.post(
        f"{base_url}/v1/customers",
        json={
            "name": f"Acme {suffix}",
            "email": f"acme-{suffix}@example.com",
            "phone": "555-0100",
        },
        headers=headers,
        timeout=5,
    )
    customer_resp.raise_for_status()
    customer_id = customer_resp.json()["id"]

    product_resp = session.post(
        f"{base_url}/v1/products",
        json={
            "name": f"Widget {suffix}",
            "sku": f"W-{suffix}",
            "price": 50.0,
        },
        headers=headers,
        timeout=5,
    )
    product_resp.raise_for_status()
    product_id = product_resp.json()["id"]

    order_payload = {
        "order_number": f"ORD-{suffix}",
        "status": "open",
        "total": 100.0,
        "customer_id": customer_id,
        "items": [
            {
                "quantity": 2,
                "unit_price": 50.0,
                "order_id": "",
                "product_id": product_id,
            }
        ],
    }
    order_resp = session.post(
        f"{base_url}/v1/orders",
        json=order_payload,
        headers=headers,
        timeout=5,
    )
    order_resp.raise_for_status()
    order_data = order_resp.json()
    order_id = order_data["id"]

    if not order_data.get("items") or not order_data.get("customer"):
        raise RuntimeError("Expected embedded items and customer in order response.")

    update_resp = session.put(
        f"{base_url}/v1/orders/{order_id}",
        json={
            "items": [
                {
                    "quantity": 1,
                    "unit_price": 50.0,
                    "order_id": "",
                    "product_id": product_id,
                }
            ]
        },
        headers=headers,
        timeout=5,
    )
    update_resp.raise_for_status()
    updated = update_resp.json()
    if not updated.get("items") or len(updated["items"]) < 2:
        raise RuntimeError("Expected appended items on update.")


def main() -> int:
    args = parse_args()
    base_url = args.base_url or f"http://127.0.0.1:{args.port}"
    database_url = build_database_url(args.db)
    proc = None
    db_path = Path(args.db)
    try:
        if not args.no_server:
            proc = start_server(args.port, database_url)
        run_flow(base_url)
        print("E2E ok: nested create/update, embedded response, auth flow")
        return 0
    finally:
        stop_server(proc)
        if proc is not None and not args.keep_db and db_path.exists():
            db_path.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
