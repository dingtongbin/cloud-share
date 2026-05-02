import { createApp } from "vue"
import { createPinia } from "pinia"
import { Lazyload } from "vant"
import App from "./App.vue"
import router from "./router"
import "./assets/style.css"

// Vant 样式
import "vant/es/toast/style"
import "vant/es/dialog/style"
import "vant/es/notify/style"

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(Lazyload)
app.mount("#app")
