"""售后申请端到端集成测试：真实路由 + 真实 MySQL。

覆盖：小程序申请售后（POST /api/after-sales）→ 建工单 + 订单转 refund →
后台售后列表（GET /admin/api/after-sales）可见。对齐 docs/test-cases.md B5-14。
"""
from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.after_sale.models import AfterSale
from app.modules.order.models import Order


def _member_token(client: TestClient) -> str:
    """mock 登录命中会员 id=1（openid=mock_openid_1）。"""
    resp = client.post(
        "/api/auth/login", json={"code": "openid_1", "nickname": "测试会员"}
    )
    assert resp.status_code == 200
    body: dict[str, Any] = resp.json()
    assert body["code"] == 0
    return str(body["data"]["token"])


def _admin_auth(client: TestClient) -> dict[str, str]:
    resp = client.post(
        "/admin/api/login", json={"username": "admin", "password": "Admin@123456"}
    )
    assert resp.status_code == 200
    token = str(resp.json()["data"]["token"])
    return {"Authorization": f"Bearer {token}"}


def test_after_sale_visible_in_admin(
    client: TestClient, db_session: Session
) -> None:
    # 清掉 conftest 种子中占用 order 1 的工单，避免 1606 重复冲突
    db_session.query(AfterSale).delete()
    db_session.commit()

    token = _member_token(client)
    auth = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/api/after-sales",
        headers=auth,
        json={"orderId": 1, "type": "refund", "reason": "商品破损"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["status"] == "applying"
    assert data["orderId"] == 1

    # 订单联动转售后中
    order = db_session.get(Order, 1)
    assert order is not None
    assert order.status == "refund"
    assert order.refund_type == "refund"
    assert order.refund_reason == "商品破损"

    # 工单已落库
    after_sale = db_session.query(AfterSale).filter(AfterSale.order_id == 1).first()
    assert after_sale is not None
    assert after_sale.status == "applying"

    # 后台售后列表可见（核心回归：此前独立工单制看不到）
    lst = client.get("/admin/api/after-sales", headers=_admin_auth(client))
    assert lst.status_code == 200
    lst_body = lst.json()
    assert lst_body["code"] == 0
    ids = [item["id"] for item in lst_body["data"]["list"]]
    assert after_sale.id in ids


def test_order_detail_reflects_after_sale_audit(
    client: TestClient, db_session: Session
) -> None:
    """后台审核通过后，小程序订单详情应反映最新售后状态（回归：此前不更新）。"""
    db_session.query(AfterSale).delete()
    db_session.commit()

    member_token = _member_token(client)
    auth = {"Authorization": f"Bearer {member_token}"}

    resp = client.post(
        "/api/after-sales",
        headers=auth,
        json={"orderId": 1, "type": "refund", "reason": "商品破损"},
    )
    assert resp.status_code == 200
    after_sale_id = int(resp.json()["data"]["id"])

    # 申请后：待审核
    before = client.get("/api/orders/1", headers=auth).json()["data"]
    assert before["statusText"] == "售后处理中"
    assert before["statusDesc"] == "退款申请已提交，请耐心等待平台审核"

    # 后台审核通过
    audit = client.put(
        f"/admin/api/after-sales/{after_sale_id}/audit",
        headers=_admin_auth(client),
        json={"approve": True, "remark": "同意退款"},
    )
    assert audit.status_code == 200
    assert audit.json()["code"] == 0

    # 小程序刷新详情看到审核通过
    after = client.get("/api/orders/1", headers=auth).json()["data"]
    assert after["statusDesc"] == "退款申请已通过，款项将原路退回"