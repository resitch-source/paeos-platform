// Typed helpers over the PAEOS API used by the UI screens.
import { apiFetch } from "./client";

export interface LoginResponse {
  access_token: string;
  expires_in: number;
}
export interface Me {
  user_id: string;
  tenant_id: string;
  permissions: string[];
}
export interface PageMeta {
  total: number;
  page: number;
  size: number;
  pages: number;
}
export interface Paged<T> {
  items: T[];
  meta: PageMeta;
}
export interface Item {
  id: string;
  code: string;
  name: string;
}
export interface Warehouse {
  id: string;
  code: string;
  name: string;
}
export interface Stock {
  item_id: string;
  warehouse_id: string;
  quantity: string;
}
export interface Customer {
  id: string;
  code: string;
  name: string;
}
export interface SalesOrder {
  id: string;
  code: string;
  status: string;
  currency: string;
}
export interface Money {
  amount_minor: number;
  currency: string;
  amount: string;
}

// --- Auth ---
export const login = (tenant_slug: string, email: string, password: string) =>
  apiFetch<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ tenant_slug, email, password }),
  });
export const me = () => apiFetch<Me>("/api/v1/auth/me");

// --- Inventory ---
export const listItems = () =>
  apiFetch<Paged<Item>>("/api/v1/inventory/items?size=100");
export const createItem = (code: string, name: string, base_uom = "kg") =>
  apiFetch<Item>("/api/v1/inventory/items", {
    method: "POST",
    body: JSON.stringify({ code, name, base_uom }),
  });
export const listWarehouses = () =>
  apiFetch<Paged<Warehouse>>("/api/v1/inventory/warehouses?size=100");
export const createWarehouse = (code: string, name: string) =>
  apiFetch<Warehouse>("/api/v1/inventory/warehouses", {
    method: "POST",
    body: JSON.stringify({ code, name }),
  });
export const stockMovement = (
  item_id: string,
  warehouse_id: string,
  movement_type: "IN" | "OUT" | "ADJUST",
  quantity: string,
) =>
  apiFetch<unknown>("/api/v1/inventory/movements", {
    method: "POST",
    body: JSON.stringify({ item_id, warehouse_id, movement_type, quantity }),
  });
export const getStock = (item_id: string, warehouse_id: string) =>
  apiFetch<Stock>(
    `/api/v1/inventory/stock?item_id=${item_id}&warehouse_id=${warehouse_id}`,
  );

// --- Trading ---
export const createCustomer = (code: string, name: string) =>
  apiFetch<Customer>("/api/v1/trading/customers", {
    method: "POST",
    body: JSON.stringify({ code, name }),
  });
export const createOrder = (
  code: string,
  customer_id: string,
  warehouse_id: string,
) =>
  apiFetch<SalesOrder>("/api/v1/trading/orders", {
    method: "POST",
    body: JSON.stringify({ code, customer_id, warehouse_id }),
  });
export const addOrderLine = (
  order_id: string,
  item_id: string,
  quantity: string,
  unit_price: string,
) =>
  apiFetch<unknown>(`/api/v1/trading/orders/${order_id}/lines`, {
    method: "POST",
    body: JSON.stringify({ item_id, quantity, unit_price }),
  });
export const orderTotal = (order_id: string) =>
  apiFetch<Money>(`/api/v1/trading/orders/${order_id}/total`);
export const transitionOrder = (order_id: string, event: string) =>
  apiFetch<SalesOrder>(`/api/v1/trading/orders/${order_id}/transition`, {
    method: "POST",
    body: JSON.stringify({ event }),
  });
export const fulfillOrder = (order_id: string) =>
  apiFetch<SalesOrder>(`/api/v1/trading/orders/${order_id}/fulfill`, {
    method: "POST",
  });
