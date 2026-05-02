import axios from "axios"
import { showToast } from "vant"
import router from "../router"

const request = axios.create({
  baseURL: "/api",
  timeout: 60000,
})

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token")
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        localStorage.removeItem("token")
        localStorage.removeItem("user")
        router.push("/login")
        showToast("登录已过期，请重新登录")
      } else if (status === 403) {
        showToast(data.detail || "权限不足")
      } else if (status === 429) {
        showToast("操作过于频繁，请稍后再试")
      } else {
        showToast(data.detail || "请求失败")
      }
    } else {
      showToast("网络连接失败")
    }
    return Promise.reject(error)
  }
)

export default request
