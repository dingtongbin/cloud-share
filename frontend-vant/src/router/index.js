import { createRouter, createWebHistory } from "vue-router"

const routes = [
  {
    path: "/login",
    name: "Login",
    component: () => import("../views/Login.vue"),
  },
  {
    path: "/",
    name: "Layout",
    component: () => import("../views/Layout.vue"),
    redirect: "/files",
    children: [
      {
        path: "files",
        name: "Files",
        component: () => import("../views/Files.vue"),
        meta: { title: "文件管理" },
      },
      {
        path: "shares",
        name: "Shares",
        component: () => import("../views/Shares.vue"),
        meta: { title: "我的分享" },
      },
      {
        path: "profile",
        name: "Profile",
        component: () => import("../views/Profile.vue"),
        meta: { title: "个人中心" },
      },
      {
        path: "settings",
        name: "Settings",
        component: () => import("../views/Settings.vue"),
        meta: { title: "个人设置" },
      },
      {
        path: "admin/users",
        name: "AdminUsers",
        component: () => import("../views/admin/Users.vue"),
        meta: { title: "用户管理", admin: true },
      },
      {
        path: "admin/records",
        name: "AdminRecords",
        component: () => import("../views/admin/Records.vue"),
        meta: { title: "下载记录", admin: true },
      },
      {
        path: "admin/logs",
        name: "AdminLogs",
        component: () => import("../views/admin/Logs.vue"),
        meta: { title: "操作日志", admin: true },
      },
      {
        path: "admin/stats",
        name: "AdminStats",
        component: () => import("../views/admin/Stats.vue"),
        meta: { title: "系统统计", admin: true },
      },
    ],
  },
  {
    path: "/share/:id",
    name: "ShareAccess",
    component: () => import("../views/ShareAccess.vue"),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("token")
  if (to.path === "/login") {
    token ? next("/") : next()
    return
  }
  if (to.path.startsWith("/share/")) {
    next()
    return
  }
  if (!token) {
    next("/login")
    return
  }
  next()
})


export default router
