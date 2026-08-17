

(function () {
    let config = {
        // API 基础地址（相对路径或完整 URL）
        API_BASE_URL: '/api',

        // 其他全局配置
        APP_TITLE: '导航收藏系统',
        MAX_UPLOAD_SIZE: 10485760,
        TIMEOUT: 120000,
        API_URLS: {
            GET_COLLECT: '/getCollect',
            SAVE_COLLECT: '/saveCollect',
            DEL_COLLECT: '/delCollect',
            BATCH_UPDATE: '/batchUpdate',
            IMPORT_COLLECT: '/importCollect',
        },
        LOGO_URL: '/favicon.ico',
    }
    config.API_URLS.EXPORT_COLLECT = config.API_BASE_URL + '/exportCollect'//拼接完整地址直接新窗口打开
    window.APP_CONFIG = config  
    // 冻结防止运行时被意外修改
    Object.freeze(window.APP_CONFIG)
})()

