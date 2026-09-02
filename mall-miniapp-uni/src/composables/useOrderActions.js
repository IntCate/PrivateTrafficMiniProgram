import { orderApi } from '@/api';

export function useOrderActions({ getOrderId, onSuccess, afterCancel, buyAgainNav = 'redirect' } = {}) {
  const resolveId = (id) => (Number.isInteger(Number(id)) && Number(id) > 0 ? Number(id) : getOrderId());
  const refresh = onSuccess || (() => {});

  const refundLabel = (status) => {
    if (status === 'paid') return '取消并退款';
    if (status === 'shipped') return '退货退款';
    return '申请售后';
  };

  const payOrder = (id) => {
    uni.showLoading({ title: '支付中' });
    setTimeout(async () => {
      try {
        const data = await orderApi.pay(resolveId(id), 'mock');
        uni.hideLoading();
        uni.showToast({ title: '支付成功', icon: 'success' });
        refresh(data);
      } catch (e) {
        uni.hideLoading();
        if (e.code === 409) {
          uni.showToast({ title: '订单已支付', icon: 'none' });
        } else {
          uni.showToast({ title: e.message || '支付失败', icon: 'none' });
        }
        refresh();
      }
    }, 800);
  };

  const cancelOrder = (id) => {
    uni.showModal({
      title: '取消订单',
      content: '确定要取消这笔订单吗？',
      confirmColor: '#F54949',
      success: async (res) => {
        if (!res.confirm) return;
        try {
          const data = await orderApi.cancel(resolveId(id), '不想要了');
          refresh(data);
          uni.showToast({ title: '订单已取消', icon: 'none' });
          if (afterCancel) afterCancel(data);
        } catch (e) {
          uni.showToast({ title: e.message || '取消失败', icon: 'none' });
        }
      },
    });
  };

  const refundOrder = (id, status) => {
    uni.showModal({
      title: refundLabel(status),
      content: '确定要提交售后申请吗？售后处理期间订单将暂停流转。',
      confirmText: '提交申请',
      confirmColor: '#F54949',
      success: async (res) => {
        if (!res.confirm) return;
        try {
          const data = await orderApi.refund(resolveId(id), { reason: '不符合预期' });
          refresh(data);
          uni.showToast({ title: '售后申请已提交', icon: 'success' });
        } catch (e) {
          uni.showToast({ title: e.message || '申请失败', icon: 'none' });
        }
      },
    });
  };

  const remindShip = async (id) => {
    try {
      await orderApi.remind(resolveId(id));
      uni.showToast({ title: '已提醒商家尽快发货', icon: 'none' });
    } catch (e) {
      uni.showToast({ title: e.message || '提醒失败', icon: 'none' });
    }
  };

  const confirmReceipt = async (id) => {
    try {
      const data = await orderApi.confirm(resolveId(id));
      refresh(data);
      uni.showToast({ title: '已确认收货', icon: 'success' });
    } catch (e) {
      uni.showToast({ title: e.message || '操作失败', icon: 'none' });
    }
  };

  const buyAgain = async (id) => {
    try {
      const data = await orderApi.buyAgain(resolveId(id));
      uni.showToast({ title: '已重新下单', icon: 'success' });
      const url = `/pages/order-detail/order-detail?id=${data.id}`;
      if (buyAgainNav === 'navigate') {
        uni.navigateTo({ url });
      } else {
        uni.redirectTo({ url });
      }
    } catch (e) {
      uni.showToast({ title: e.message || '再次购买失败', icon: 'none' });
    }
  };

  return { payOrder, cancelOrder, refundLabel, refundOrder, remindShip, confirmReceipt, buyAgain };
}
