<script>
import { ensureLogin } from '@/api/auth';

export default {
  onLaunch() {
    ensureLogin().catch(() => {});
  },
};
</script>

<style lang="scss">
/* 全局基础样式 */
page {
  font-family: "Inter", "Noto Sans SC", "PingFang SC", "MiSans", "Microsoft YaHei", system-ui, sans-serif;
  background-color: #FFFBF8;
  color: #1C1C1E;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  height: 40px;
  background-color: $mall-card;
  border: 1px solid $mall-border;
  border-radius: 9999px;
}

.search-input {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  color: $mall-foreground;
}
</style>