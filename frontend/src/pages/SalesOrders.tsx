import { useCallback, useEffect, useState } from "react";
import {
  addOrderLine,
  createCustomer,
  createOrder,
  fulfillOrder,
  getStock,
  listItems,
  listWarehouses,
  orderTotal,
  transitionOrder,
  type Customer,
  type Item,
  type Money,
  type SalesOrder,
  type Warehouse,
} from "../api/paeos";

function msg(e: unknown): string {
  return e instanceof Error ? e.message : "Request failed";
}

// The trading API exposes create/act endpoints (no list), so this is a guided
// flow over entities created in this session.
export function SalesOrders() {
  const [items, setItems] = useState<Item[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [error, setError] = useState("");

  const [custCode, setCustCode] = useState("C-001");
  const [custName, setCustName] = useState("Manila Oil Mills");
  const [customer, setCustomer] = useState<Customer | null>(null);

  const [orderCode, setOrderCode] = useState("SO-001");
  const [orderWh, setOrderWh] = useState("");
  const [order, setOrder] = useState<SalesOrder | null>(null);

  const [lineItem, setLineItem] = useState("");
  const [lineQty, setLineQty] = useState("100");
  const [linePrice, setLinePrice] = useState("80.00");
  const [total, setTotal] = useState<Money | null>(null);

  const [note, setNote] = useState("");

  const load = useCallback(async () => {
    try {
      const [it, wh] = await Promise.all([listItems(), listWarehouses()]);
      setItems(it.items);
      setWarehouses(wh.items);
    } catch (e) {
      setError(msg(e));
    }
  }, []);
  useEffect(() => {
    void load();
  }, [load]);

  const step = order
    ? order.status === "draft"
      ? "line"
      : order.status
    : customer
      ? "order"
      : "customer";

  const run = async (fn: () => Promise<void>) => {
    setError("");
    try {
      await fn();
    } catch (e) {
      setError(msg(e));
    }
  };

  const mkCustomer = () =>
    run(async () => setCustomer(await createCustomer(custCode, custName)));

  const mkOrder = () =>
    run(async () => {
      if (!customer) return;
      setOrder(await createOrder(orderCode, customer.id, orderWh));
    });

  const addLine = () =>
    run(async () => {
      if (!order) return;
      await addOrderLine(order.id, lineItem, lineQty, linePrice);
      setTotal(await orderTotal(order.id));
    });

  const confirm = () =>
    run(async () => {
      if (!order) return;
      setOrder(await transitionOrder(order.id, "confirm"));
    });

  const fulfil = () =>
    run(async () => {
      if (!order) return;
      const updated = await fulfillOrder(order.id);
      setOrder(updated);
      if (lineItem && orderWh) {
        const s = await getStock(lineItem, orderWh);
        setNote(`Fulfilled. On-hand for the ordered item is now ${s.quantity}.`);
      }
    });

  const reset = () => {
    setCustomer(null);
    setOrder(null);
    setTotal(null);
    setNote("");
    setError("");
  };

  return (
    <main className="page">
      <h1>Sales Orders</h1>
      <p className="sub">
        Guided flow: create a customer → order → line (exact Money) → confirm →
        fulfil (posts stock OUT via the central service). Current step:{" "}
        <span className="pill">{step}</span>
      </p>
      {error && <p className="err">{error}</p>}

      <div className="card">
        <h2 style={{ marginTop: 0 }}>1 · Customer</h2>
        {customer ? (
          <p className="ok">
            Created customer {customer.code} — {customer.name}
          </p>
        ) : (
          <div className="row">
            <div>
              <label>Code</label>
              <input value={custCode} onChange={(e) => setCustCode(e.target.value)} />
            </div>
            <div className="grow">
              <label>Name</label>
              <input
                style={{ width: "100%" }}
                value={custName}
                onChange={(e) => setCustName(e.target.value)}
              />
            </div>
            <button disabled={!custCode || !custName} onClick={mkCustomer}>
              Create customer
            </button>
          </div>
        )}
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>2 · Order</h2>
        {order ? (
          <p className="ok">
            Order {order.code} · status <span className="pill">{order.status}</span>
          </p>
        ) : (
          <div className="row">
            <div>
              <label>Code</label>
              <input value={orderCode} onChange={(e) => setOrderCode(e.target.value)} />
            </div>
            <div>
              <label>Warehouse</label>
              <select value={orderWh} onChange={(e) => setOrderWh(e.target.value)}>
                <option value="">Select…</option>
                {warehouses.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.code} — {w.name}
                  </option>
                ))}
              </select>
            </div>
            <button disabled={!customer || !orderCode || !orderWh} onClick={mkOrder}>
              Create order
            </button>
          </div>
        )}
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>3 · Line & total</h2>
        <div className="row">
          <div>
            <label>Item</label>
            <select value={lineItem} onChange={(e) => setLineItem(e.target.value)}>
              <option value="">Select…</option>
              {items.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.code} — {i.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Quantity</label>
            <input value={lineQty} onChange={(e) => setLineQty(e.target.value)} />
          </div>
          <div>
            <label>Unit price</label>
            <input value={linePrice} onChange={(e) => setLinePrice(e.target.value)} />
          </div>
          <button
            disabled={!order || order.status !== "draft" || !lineItem}
            onClick={addLine}
          >
            Add line
          </button>
        </div>
        {total && (
          <p className="ok">
            Order total: {total.amount} {total.currency}
          </p>
        )}
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>4 · Confirm & fulfil</h2>
        <div className="row">
          <button disabled={!order || order.status !== "draft"} onClick={confirm}>
            Confirm
          </button>
          <button
            disabled={!order || order.status !== "confirmed"}
            onClick={fulfil}
          >
            Fulfil
          </button>
          <button className="secondary" onClick={reset}>
            Start over
          </button>
        </div>
        {note && <p className="ok">{note}</p>}
      </div>
    </main>
  );
}
