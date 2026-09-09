import { useCallback, useEffect, useState } from "react";
import {
  createItem,
  createWarehouse,
  getStock,
  listItems,
  listWarehouses,
  stockMovement,
  type Item,
  type Warehouse,
} from "../api/paeos";

function msg(e: unknown): string {
  return e instanceof Error ? e.message : "Request failed";
}

export function Inventory() {
  const [items, setItems] = useState<Item[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [error, setError] = useState("");

  const [itemCode, setItemCode] = useState("");
  const [itemName, setItemName] = useState("");
  const [whCode, setWhCode] = useState("");
  const [whName, setWhName] = useState("");

  const [mItem, setMItem] = useState("");
  const [mWh, setMWh] = useState("");
  const [mQty, setMQty] = useState("100");
  const [stockMsg, setStockMsg] = useState("");

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

  const addItem = async () => {
    setError("");
    try {
      await createItem(itemCode, itemName);
      setItemCode("");
      setItemName("");
      await load();
    } catch (e) {
      setError(msg(e));
    }
  };

  const addWarehouse = async () => {
    setError("");
    try {
      await createWarehouse(whCode, whName);
      setWhCode("");
      setWhName("");
      await load();
    } catch (e) {
      setError(msg(e));
    }
  };

  const doStockIn = async () => {
    setError("");
    setStockMsg("");
    try {
      await stockMovement(mItem, mWh, "IN", mQty);
      const s = await getStock(mItem, mWh);
      setStockMsg(`On-hand for that item/warehouse: ${s.quantity}`);
    } catch (e) {
      setError(msg(e));
    }
  };

  return (
    <main className="page">
      <h1>Inventory</h1>
      <p className="sub">
        Items, warehouses, and stock — all changes go through the central
        inventory service.
      </p>
      {error && <p className="err">{error}</p>}

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Add item</h2>
        <div className="row">
          <div>
            <label>Code</label>
            <input value={itemCode} onChange={(e) => setItemCode(e.target.value)} />
          </div>
          <div className="grow">
            <label>Name</label>
            <input
              style={{ width: "100%" }}
              value={itemName}
              onChange={(e) => setItemName(e.target.value)}
            />
          </div>
          <button disabled={!itemCode || !itemName} onClick={addItem}>
            Add item
          </button>
        </div>
        <h2>Items ({items.length})</h2>
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
            </tr>
          </thead>
          <tbody>
            {items.map((i) => (
              <tr key={i.id}>
                <td>{i.code}</td>
                <td>{i.name}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Add warehouse</h2>
        <div className="row">
          <div>
            <label>Code</label>
            <input value={whCode} onChange={(e) => setWhCode(e.target.value)} />
          </div>
          <div className="grow">
            <label>Name</label>
            <input
              style={{ width: "100%" }}
              value={whName}
              onChange={(e) => setWhName(e.target.value)}
            />
          </div>
          <button disabled={!whCode || !whName} onClick={addWarehouse}>
            Add warehouse
          </button>
        </div>
        <h2>Warehouses ({warehouses.length})</h2>
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
            </tr>
          </thead>
          <tbody>
            {warehouses.map((w) => (
              <tr key={w.id}>
                <td>{w.code}</td>
                <td>{w.name}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Stock in</h2>
        <div className="row">
          <div>
            <label>Item</label>
            <select value={mItem} onChange={(e) => setMItem(e.target.value)}>
              <option value="">Select…</option>
              {items.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.code} — {i.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Warehouse</label>
            <select value={mWh} onChange={(e) => setMWh(e.target.value)}>
              <option value="">Select…</option>
              {warehouses.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.code} — {w.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Quantity</label>
            <input value={mQty} onChange={(e) => setMQty(e.target.value)} />
          </div>
          <button disabled={!mItem || !mWh || !mQty} onClick={doStockIn}>
            Stock in
          </button>
        </div>
        {stockMsg && <p className="ok">{stockMsg}</p>}
      </div>
    </main>
  );
}
