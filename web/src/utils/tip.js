import { ElMessage, ElLoading, ElMessageBox } from 'element-plus'
let loadingInstance = null
let loadingCount = 0 // 请求计数器
export function successTip(message) {
    ElMessage({
        message: message,
        type: 'success',
    })
}
export function errorTip(message) {
    ElMessage.error(message)

}
export function loading() {
    loadingCount++
    if (loadingCount === 1) {
        loadingInstance = ElLoading.service({
            lock: true,
            text: '加载中...',
            background: 'rgba(0, 0, 0, 0.5)'
        })
    }
}

export function loadingClose() {
    loadingCount--
    if (loadingCount <= 0) {
        loadingInstance?.close()
        loadingCount = 0
    }
}
export function customConfirm(msg) {
    return ElMessageBox.confirm(msg)
        // .then(() => {
        //     done()
        // })
        // .catch(() => {
        //     // catch error
        // })
}