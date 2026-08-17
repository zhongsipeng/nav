import { errorTip } from './tip';
export function openSafeUrl(url) {
    // 验证 URL 合法性（示例：仅允许 https）
    if (/^https?:\/\//.test(url)) {
        const newWindow = window.open(url, '_blank');
        if (newWindow) {
            newWindow.opener = null; // 防止新窗口访问原窗口
        }
    } else {
        // this.$message.error('无效的 URL');
        errorTip('无效的 URL');
    }
}