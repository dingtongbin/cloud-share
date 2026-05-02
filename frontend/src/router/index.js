import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('../views/Layout.vue'),
    redirect: '/files',
    children: [
      {
        path: 'files',
        name: 'Files',
        component: () => import('../views/Files.vue'),
        meta: { title: '文件管理', icon: 'Folder' },
      },
      {
        path: 'shares',
        name: 'Shares',
        component: () => import('../views/Shares.vue'),
        meta: { title: '我的分享', icon: 'Share' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../views/Settings.vue'),
        meta: { title: '个人设置', icon: 'Setting' },
      },
      {
        path: 'admin/users',
        name: 'AdminUsers',
        component: () => import('../views/admin/Users.vue'),
        meta: { title: '用户管理', icon: 'User', admin: true },
      },
      {
        path: 'admin/records',
        name: 'AdminRecords',
        component: () => import('../views/admin/Records.vue'),
        meta: { title: '下载记录', icon: 'Document', admin: true },
      },
    ],
  },
  {
    path: '/share/:id',
    name: 'ShareAccess',
    component: () => import('../views/ShareAccess.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.path === '/login') {
    if (token) {
      next('/')
    } else {
      next()
    }
    return
  }
  
  if (to.path.startsWith('/share/')) {
    next()
    return
  }
  
  if (!token) {
    next('/login')
    return
  }
  
  next()
})

export default router
