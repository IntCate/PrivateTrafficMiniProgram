"""售后申请端到端集成测试：真实路由 + 真实 MySQL。

覆盖：小程序申请售后（POST /api/after-sales）→ 建工单 + 订单转 refund →
后台售后列表（GET /admin/api/after-sales）可见。对齐 docs/test-cases.md B5-14。
"""
from __future__ import annotations

from decimal import Decimal
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
        json={
            "orderId": 1,
            "type": "refund",
            "reason": "商品破损",
            "images": ["/uploads/after_sale/demo.jpg"],
        },
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
    item = next(i for i in lst_body["data"]["list"] if i["id"] == after_sale.id)
    assert item["images"] == ["/uploads/after_sale/demo.jpg"]


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

    # 申请后：待审核（statusText 与列表一致为"申请中"）
    before = client.get("/api/orders/1", headers=auth).json()["data"]
    assert before["statusText"] == "申请中"
    assert before["statusDesc"] == "退款申请已提交，请耐心等待平台审核"

    # 后台审核通过
    audit = client.put(
        f"/admin/api/after-sales/{after_sale_id}/audit",
        headers=_admin_auth(client),
        json={"approve": True, "remark": "同意退款"},
    )
    assert audit.status_code == 200
    assert audit.json()["code"] == 0

    # 小程序刷新详情看到审核通过（statusText 跟随售后状态）
    after = client.get("/api/orders/1", headers=auth).json()["data"]
    assert after["statusText"] == "已通过"
    assert after["statusDesc"] == "退款申请已通过，款项将原路退回"

    # 小程序订单列表（售后/退款 tab）也应反映审核进度，而非固定"售后中"
    lst = client.get("/api/orders?status=refund", headers=auth).json()["data"]
    items = lst["list"] if isinstance(lst, dict) and "list" in lst else lst.get("items", [])
    first = next(i for i in items if i["id"] == 1)
    assert first["statusText"] == "已通过"


def test_refund_badge_and_sorting(
    client: TestClient, db_session: Session
) -> None:
    """售后角标只统计"申请中"，且售后 tab 让申请中的单子排最前。

    构造：order1 → refund+申请中(applying)；order2 → refund+已通过(approved)。
    角标 refund 应为 1（而非 2），列表首个应为 order1。
    """
    db_session.query(AfterSale).delete()
    o1 = db_session.get(Order, 1)
    o2 = db_session.get(Order, 2)
    assert o1 is not None and o2 is not None
    o1.status = "refund"
    o2.status = "refund"
    db_session.add_all(
        [
            AfterSale(
                order_id=1, user_id=1, type="refund", reason="a",
                amount=Decimal("100.00"), status="applying", audit_remark=None,
            ),
            AfterSale(
                order_id=2, user_id=1, type="refund", reason="b",
                amount=Decimal("50.00"), status="approved", audit_remark="同意",
            ),
        ]
    )
    db_session.commit()

    token = _member_token(client)
    auth = {"Authorization": f"Bearer {token}"}

    # 角标：只有 1 个"申请中"
    overview = client.get("/api/member/overview", headers=auth).json()["data"]
    assert overview["orderStats"]["refund"] == 1

    # 排序：申请中(order1) 排在 已通过(order2) 前
    lst = client.get("/api/orders?status=refund", headers=auth).json()["data"]
    items = lst["list"] if isinstance(lst, dict) and "list" in lst else lst.get("items", [])
    ids = [i["id"] for i in items]
    assert ids == [1, 2]


def test_after_sale_reason_and_type_validation(
    client: TestClient, db_session: Session
) -> None:
    """售后申请需填写原因、类型合法（1402）。"""
    db_session.query(AfterSale).delete()
    db_session.commit()
    auth = {"Authorization": f"Bearer {_member_token(client)}"}

    # 原因必填
    resp = client.post(
        "/api/after-sales", headers=auth,
        json={"orderId": 1, "type": "refund", "reason": "  "},
    )
    assert resp.status_code == 200
    assert resp.json()["code"] == 1402

    # 类型非法
    resp = client.post(
        "/api/after-sales", headers=auth,
        json={"orderId": 1, "type": "weird", "reason": "破损"},
    )
    assert resp.status_code == 200
    assert resp.json()["code"] == 1402

    # 合法申请
    resp = client.post(
        "/api/after-sales", headers=auth,
        json={"orderId": 1, "type": "refund", "reason": " 商品破损 "},
    )
    assert resp.json()["code"] == 0
    assert resp.json()["data"]["reason"] == "商品破损"  # 已去除首尾空格


def test_after_sale_refund_type_follows_choice(
    client: TestClient, db_session: Session
) -> None:
    """订单 refund_type 跟随用户选择的售后类型（而非按订单状态推断）。"""
    db_session.query(AfterSale).delete()
    o2 = db_session.get(Order, 2)
    assert o2 is not None
    o2.status = "completed"
    db_session.commit()

    auth = {"Authorization": f"Bearer {_member_token(client)}"}
    resp = client.post(
        "/api/after-sales", headers=auth,
        json={"orderId": 2, "type": "return", "reason": "不合适"},
    )
    assert resp.json()["code"] == 0
    assert resp.json()["data"]["type"] == "return"

    db_session.refresh(o2)
    assert o2.refund_type == "return"


def test_upload_image_default_after_sale(client: TestClient, db_session: Session) -> None:
    """会员默认上传到 after_sale，返回 /uploads/after_sale/ 相对 URL。"""
    auth = {"Authorization": f"Bearer {_member_token(client)}"}
    resp = client.post(
        "/api/upload",
        headers=auth,
        files={"file": ("proof.png", b"\x89PNG\r\n\x1a\n000", "image/png")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["url"].startswith("/uploads/after_sale/")


def test_upload_image_avatar_category(client: TestClient, db_session: Session) -> None:
    """上传头像用途 category=avatar → /uploads/avatar/ 相对 URL。"""
    auth = {"Authorization": f"Bearer {_member_token(client)}"}
    resp = client.post(
        "/api/upload",
        headers=auth,
        data={"category": "avatar"},
        files={"file": ("avatar.png", b"\x89PNG\r\n\x1a\n000", "image/png")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["url"].startswith("/uploads/avatar/")


def test_upload_image_invalid_category(client: TestClient, db_session: Session) -> None:
    """非法上传用途 → 400。"""
    auth = {"Authorization": f"Bearer {_member_token(client)}"}
    resp = client.post(
        "/api/upload",
        headers=auth,
        data={"category": "evil"},
        files={"file": ("proof.png", b"\x89PNG\r\n\x1a\n000", "image/png")},
    )
    assert resp.status_code == 400