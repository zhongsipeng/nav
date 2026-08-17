


import { createMemoryHistory, createWebHashHistory, createRouter } from 'vue-router'


const routes = [
  { path: '/', redirect: '/home' },
  { path: '/home', component: () => import('@/view/Home.vue') },
  {
    path: '/grid', component: () => import('@/layout/Grid.vue'),
    children: [
      { path: 'home', component: () => import('@/view/Home.vue'), meta: { keepAlive: true } },
      // { path: 'gamesearch', component: () => import('@/view/GameSeach.vue'), meta: { keepAlive: true } },
    ]
  },

]

const router = createRouter({
  // history: createMemoryHistory(),
  history: createWebHashHistory(),
  routes,
})

export default router;