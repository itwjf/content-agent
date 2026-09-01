import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Products from '../views/Products.vue'
import Monitor from '../views/Monitor.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/monitor',
      name: 'monitor',
      component: Monitor
    },
    {
      path: '/products',
      name: 'products',
      component: Products
    }
  ]
})

export default router
