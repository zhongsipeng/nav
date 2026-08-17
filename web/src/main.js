import './assets/main.css'
import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import router from './router';
import zhCn from 'element-plus/es/locale/lang/zh-cn'
const app = createApp(App)
.use(ElementPlus, {
    locale: zhCn,
})
.use(router)

app.config.globalProperties.$config = 123

app.mount('#app')