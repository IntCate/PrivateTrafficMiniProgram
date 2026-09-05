"""后台管理 API 集成测试：真实路由 + 鉴权 + 权限矩阵 + 完整请求链路。

对齐 docs/api-design.md §13 与 auth.md §2.2 权限矩阵。使用 SQLite 内存库（conftest）。
"""
from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def _login(client: TestClient, username: str, password: str) -> str:
    resp = client.post("/admin/api/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    body: dict[str, Any] = resp.json()
    assert body["code"] == 0
    return str(body["data"]["token"])


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---- 登录 ----

def test_login_ok(client: TestClient) -> None:
    resp = client.post("/admin/api/login", json={"username": "admin", "password": "Admin@123456"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["token"]
    assert body["data"]["admin"]["username"] == "admin"
    assert body["data"]["admin"]["role"] == "admin"
    assert "password" not in body["data"]["admin"]


def test_login_wrong_password(client: TestClient) -> None:
    resp = client.post("/admin/api/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 200
    assert resp.json()["code"] == 1701


def test_login_not_found(client: TestClient) -> None:
    resp = client.post("/admin/api/login", json={"username": "nobody", "password": "x"})
    assert resp.status_code == 200
    assert resp.json()["code"] == 1701


def test_login_validation_error(client: TestClient) -> None:
    resp = client.post("/admin/api/login", json={"username": "", "password": ""})
    assert resp.status_code == 400
    assert resp.json()["code"] == 400


# ---- 鉴权 ----

def test_require_token(client: TestClient) -> None:
    resp = client.get("/admin/api/admins")
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


def test_invalid_token(client: TestClient) -> None:
    resp = client.get("/admin/api/admins", headers=_auth("bad.token.here"))
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


# ---- 权限矩阵 ----

def test_admin_can_list_admins(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/admins", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 3


def test_operator_forbidden_list_admins(client: TestClient) -> None:
    token = _login(client, "operator", "123456")
    resp = client.get("/admin/api/admins", headers=_auth(token))
    assert resp.status_code == 403
    assert resp.json()["code"] == 403


def test_finance_forbidden_list_admins(client: TestClient) -> None:
    token = _login(client, "finance", "123456")
    resp = client.get("/admin/api/admins", headers=_auth(token))
    assert resp.status_code == 403
    assert resp.json()["code"] == 403


def test_operator_can_list_products(client: TestClient) -> None:
    token = _login(client, "operator", "123456")
    resp = client.get("/admin/api/products", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["code"] == 0


def test_finance_can_list_orders(client: TestClient) -> None:
    token = _login(client, "finance", "123456")
    resp = client.get("/admin/api/orders", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["code"] == 0


def test_finance_forbidden_ship_order(client: TestClient) -> None:
    token = _login(client, "finance", "123456")
    resp = client.put("/admin/api/orders/1/ship", json={"tracking_no": "SF1"}, headers=_auth(token))
    assert resp.status_code == 403
    assert resp.json()["code"] == 403


def test_operator_forbidden_update_member_status(client: TestClient) -> None:
    token = _login(client, "operator", "123456")
    resp = client.put("/admin/api/members/1/status", json={"status": 0}, headers=_auth(token))
    assert resp.status_code == 403
    assert resp.json()["code"] == 403


def test_operator_forbidden_update_config(client: TestClient) -> None:
    token = _login(client, "operator", "123456")
    resp = client.put(
        "/admin/api/configs/order_timeout_seconds",
        json={"config_value": "3600"},
        headers=_auth(token),
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == 403


# ---- 管理员 ----

def test_create_admin_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.post(
        "/admin/api/admins",
        json={"username": "op1", "password": "123456", "role": "operator"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["username"] == "op1"
    assert body["data"]["role"] == "operator"


def test_create_admin_duplicate(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.post(
        "/admin/api/admins",
        json={"username": "admin", "password": "123456"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["code"] == 1702


def test_update_admin_status_self_disable(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.put("/admin/api/admins/1/status", json={"status": 0}, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["code"] == 1703


def test_update_admin_status_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.put("/admin/api/admins/2/status", json={"status": 0}, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == 0


# ---- 商品 ----

def test_list_products_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/products", headers=_auth(token))
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 1
    assert body["data"]["list"][0]["name"] == "测试商品"


def test_list_products_keyword(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/products?keyword=不存在", headers=_auth(token))
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 0


def test_get_product_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/products/1", headers=_auth(token))
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["price"] == "99.00"


def test_get_product_not_found(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/products/999", headers=_auth(token))
    assert resp.json()["code"] == 404


def test_create_product_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.post(
        "/admin/api/products",
        json={
            "product_no": "P1000",
            "category_id": 1,
            "name": "新品",
            "price": "9.90",
            "main_image": "https://img.example.com/p.png",
        },
        headers=_auth(token),
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["name"] == "新品"


def test_create_product_category_not_found(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.post(
        "/admin/api/products",
        json={
            "product_no": "P1001",
            "category_id": 999,
            "name": "新品",
            "price": "9.90",
            "main_image": "https://img.example.com/p.png",
        },
        headers=_auth(token),
    )
    assert resp.json()["code"] == 404


def test_update_product_status_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.put("/admin/api/products/1/status", json={"status": 0}, headers=_auth(token))
    assert resp.json()["data"]["status"] == 0


def test_delete_product_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.delete("/admin/api/products/1", headers=_auth(token))
    assert resp.json()["code"] == 0
    assert resp.json()["data"]["deleted"] is True


# ---- 商品 SKU ----

def test_list_product_skus_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/products/1/skus", headers=_auth(token))
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["list"][0]["sku_code"] == "SKU0001"


def test_list_product_skus_not_found(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/products/999/skus", headers=_auth(token))
    assert resp.json()["code"] == 404


def test_create_product_sku_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.post(
        "/admin/api/products/1/skus",
        json={"sku_code": "SKU1000", "sku_text": "白色；40", "price": "100.00", "stock": 50},
        headers=_auth(token),
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["sku_code"] == "SKU1000"


def test_create_product_sku_product_not_found(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.post(
        "/admin/api/products/999/skus",
        json={"sku_code": "SKU-X", "sku_text": "x", "price": "10.00", "stock": 1},
        headers=_auth(token),
    )
    assert resp.json()["code"] == 404


def test_update_product_sku_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.put(
        "/admin/api/products/1/skus/1",
        json={"price": "88.00", "stock": 5},
        headers=_auth(token),
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["price"] == "88.00"
    assert body["data"]["stock"] == 5


def test_update_product_sku_not_found(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.put(
        "/admin/api/products/1/skus/999",
        json={"price": "88.00"},
        headers=_auth(token),
    )
    assert resp.json()["code"] == 404


def test_delete_product_sku_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.delete("/admin/api/products/1/skus/1", headers=_auth(token))
    assert resp.json()["code"] == 0
    assert resp.json()["data"]["deleted"] is True


# ---- 分类 ----

def test_list_categories_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/categories", headers=_auth(token))
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["list"][0]["name"] == "数码"


def test_create_category_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.post(
        "/admin/api/categories", json={"name": "新分类"}, headers=_auth(token)
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["name"] == "新分类"


def test_delete_category_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.delete("/admin/api/categories/2", headers=_auth(token))
    assert resp.json()["code"] == 0


# ---- 订单 ----

def test_list_orders_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/orders", headers=_auth(token))
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 2


def test_list_orders_by_status(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/orders?status=paid", headers=_auth(token))
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 1


def test_get_order_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/orders/1", headers=_auth(token))
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["order_no"] == "K0000000001"


def test_ship_order_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.put(
        "/admin/api/orders/1/ship", json={"tracking_no": "SF123"}, headers=_auth(token)
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "shipped"


def test_ship_order_wrong_status(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.put("/admin/api/orders/2/ship", json={}, headers=_auth(token))
    assert resp.json()["code"] == 1402


# ---- 会员 ----

def test_list_members_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/members", headers=_auth(token))
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 1
    assert body["data"]["list"][0]["nickname"] == "测试会员"


def test_update_member_status_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.put("/admin/api/members/1/status", json={"status": 0}, headers=_auth(token))
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["status"] == 0


# ---- 运营位 ----

def test_list_banners_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/banners", headers=_auth(token))
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["list"][0]["title"] == "主横幅"


def test_create_banner_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.post(
        "/admin/api/banners",
        json={"position": "hero", "title": "新横幅", "image": "https://img.example.com/x.png"},
        headers=_auth(token),
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["title"] == "新横幅"


# ---- 优惠券 ----

def test_list_coupons_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/coupons", headers=_auth(token))
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["list"][0]["name"] == "满减券"


def test_create_coupon_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.post(
        "/admin/api/coupons",
        json={"name": "新券", "type": "cash", "amount": "5.00"},
        headers=_auth(token),
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["name"] == "新券"


def test_grant_coupon_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.post(
        "/admin/api/coupons/1/grant", json={"user_id": 1, "count": 2}, headers=_auth(token)
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["granted"] == 2


def test_grant_coupon_member_not_found(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.post(
        "/admin/api/coupons/1/grant", json={"user_id": 999, "count": 1}, headers=_auth(token)
    )
    assert resp.json()["code"] == 404


# ---- 售后 ----

def test_list_after_sales_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/after-sales", headers=_auth(token))
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 1


def test_audit_after_sale_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.put(
        "/admin/api/after-sales/1/audit",
        json={"approve": True, "remark": "同意"},
        headers=_auth(token),
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "approved"
    assert body["data"]["audit_remark"] == "同意"


def test_audit_after_sale_reject(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.put(
        "/admin/api/after-sales/1/audit",
        json={"approve": False, "remark": "驳回"},
        headers=_auth(token),
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "rejected"


def test_audit_after_sale_wrong_status(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    client.put(
        "/admin/api/after-sales/1/audit",
        json={"approve": True},
        headers=_auth(token),
    )
    resp = client.put(
        "/admin/api/after-sales/1/audit",
        json={"approve": True},
        headers=_auth(token),
    )
    assert resp.json()["code"] == 1607
    assert resp.json()["message"] == "售后单状态不允许审核"


# ---- 数据概览 ----

def test_dashboard_summary_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/dashboard/summary", headers=_auth(token))
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["order_count"] == 2
    assert body["data"]["member_count"] == 1
    assert body["data"]["product_count"] == 1
    assert body["data"]["pending_order_count"] == 1
    assert body["data"]["total_sales"] == "100.00"


# ---- 系统配置 ----

def test_list_configs_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.get("/admin/api/configs", headers=_auth(token))
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["list"][0]["config_key"] == "order_timeout_seconds"


def test_update_config_ok(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.put(
        "/admin/api/configs/order_timeout_seconds",
        json={"config_value": "3600"},
        headers=_auth(token),
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["config_value"] == "3600"


def test_update_config_not_found(client: TestClient) -> None:
    token = _login(client, "admin", "Admin@123456")
    resp = client.put(
        "/admin/api/configs/not_exist",
        json={"config_value": "3600"},
        headers=_auth(token),
    )
    assert resp.json()["code"] == 404
