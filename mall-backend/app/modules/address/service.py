"""收货地址模块业务逻辑：列表 / 新增 / 编辑 / 删除 / 设默认。

对齐 docs/api-design.md §8 与 docs/test-cases.md B4。
"""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.address.models import ADDRESS_MAX_COUNT, ShippingAddress
from app.modules.address.repository import AddressRepository
from app.modules.address.schemas import AddressOut, AddressRequest

PHONE_RE = re.compile(r"^1\d{10}$")


def _to_out(address: ShippingAddress) -> dict:
    """ORM → 对外 DTO（regionText = "省 市 区"）。"""
    return AddressOut(
        id=address.id,
        name=address.name,
        phone=address.phone,
        province=address.province,
        city=address.city,
        district=address.district,
        detail=address.detail,
        is_default=address.is_default,
        region_text=f"{address.province} {address.city} {address.district}",
    ).model_dump(by_alias=True)


def _validate(req: AddressRequest) -> None:
    """参数校验（对齐 api-design §8.2 / test-cases B4-3）。

    - 姓名非空、手机号 ^1\\d{10}$、省市区与详细地址非空 → 不合法返回 400
    """
    if not req.name or not req.name.strip():
        raise BizException(400, "姓名不能为空")
    if not PHONE_RE.match(req.phone or ""):
        raise BizException(400, "手机号格式不正确")
    if not req.province or not req.city or not req.district:
        raise BizException(400, "省市区不能为空")
    if not req.detail or not req.detail.strip():
        raise BizException(400, "详细地址不能为空")


def list_addresses(db: Session, user_id: int) -> dict:
    """地址列表（对齐 api-design §8.1）：默认优先、创建时间倒序。"""
    repo = AddressRepository(db)
    items = repo.list_by_user(user_id)
    return {"list": [_to_out(a) for a in items]}


def create_address(db: Session, user_id: int, req: AddressRequest) -> dict:
    """新增地址（对齐 api-design §8.2 / test-cases B4-1/B4-2/B4-3）。

    - 数量达到上限 20 → 1301（data.maxCount）
    - 用户首个地址自动置为默认
    - isDefault=true 时同用户其他地址默认标识置 0（唯一默认）
    """
    _validate(req)
    repo = AddressRepository(db)
    count = repo.count_by_user(user_id)
    if count >= ADDRESS_MAX_COUNT:
        raise BizException(
            1301,
            f"地址数量已达上限（{ADDRESS_MAX_COUNT} 条）",
            {"maxCount": ADDRESS_MAX_COUNT},
        )

    is_default = req.is_default or count == 0
    if is_default:
        repo.clear_default(user_id)

    address = ShippingAddress(
        user_id=user_id,
        name=req.name.strip(),
        phone=req.phone,
        province=req.province,
        city=req.city,
        district=req.district,
        detail=req.detail.strip(),
        is_default=is_default,
    )
    repo.save(address)
    db.commit()
    return _to_out(address)


def update_address(db: Session, user_id: int, address_id: int, req: AddressRequest) -> dict:
    """编辑地址（对齐 api-design §8.3 / test-cases B4-4/B4-6）。

    请求体全字段必传、整体覆盖；isDefault=true 时同用户其他地址默认标识置 0。
    """
    _validate(req)
    repo = AddressRepository(db)
    address = repo.get_owned(user_id, address_id)
    if address is None:
        raise BizException(404, "地址不存在")

    if req.is_default:
        repo.clear_default(user_id)

    address.name = req.name.strip()
    address.phone = req.phone
    address.province = req.province
    address.city = req.city
    address.district = req.district
    address.detail = req.detail.strip()
    address.is_default = req.is_default
    repo.save(address)
    db.commit()
    return _to_out(address)


def delete_address(db: Session, user_id: int, address_id: int) -> dict:
    """删除地址（对齐 api-design §8.4 / test-cases B4-5/B4-6）。

    逻辑删除（deleted=1）；删除默认地址后，若存在剩余地址，最新一条自动置为默认。
    """
    repo = AddressRepository(db)
    address = repo.get_owned(user_id, address_id)
    if address is None:
        raise BizException(404, "地址不存在")

    address.deleted = True
    repo.save(address)
    if address.is_default:
        latest = repo.latest(user_id)
        if latest is not None:
            latest.is_default = True
            repo.save(latest)
    db.commit()
    return list_addresses(db, user_id)


def set_default(db: Session, user_id: int, address_id: int) -> dict:
    """设为默认（对齐 api-design §8.5 / test-cases B4-4/B4-6）：同用户唯一默认。"""
    repo = AddressRepository(db)
    address = repo.get_owned(user_id, address_id)
    if address is None:
        raise BizException(404, "地址不存在")

    repo.clear_default(user_id)
    address.is_default = True
    repo.save(address)
    db.commit()
    return list_addresses(db, user_id)
