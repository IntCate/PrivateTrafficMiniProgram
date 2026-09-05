import { onUnmounted, ref } from 'vue';

export function useCountdown() {
  const remainText = ref('');
  const expired = ref(false);
  let timer = null;

  const pad = (n) => String(n).padStart(2, '0');

  const format = (ms) => {
    if (ms <= 0) return '00:00:00';
    const total = Math.floor(ms / 1000);
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    const s = total % 60;
    return `${pad(h)}:${pad(m)}:${pad(s)}`;
  };

  const start = (deadline) => {
    stop();
    if (!deadline) {
      remainText.value = '';
      expired.value = false;
      return;
    }
    const target = new Date(deadline).getTime();
    const tick = () => {
      const diff = target - Date.now();
      if (diff <= 0) {
        remainText.value = '00:00:00';
        expired.value = true;
        stop();
        return;
      }
      remainText.value = format(diff);
      expired.value = false;
    };
    tick();
    timer = setInterval(tick, 1000);
  };

  const stop = () => {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  };

  onUnmounted(stop);

  return { remainText, expired, start, stop };
}
