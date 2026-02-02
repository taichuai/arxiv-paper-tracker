import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import PaperList from './views/PaperList.vue'
import PaperDetail from './views/PaperDetail.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: PaperList },
    { path: '/paper/:id', component: PaperDetail, props: true }
  ]
})

createApp(App).use(router).mount('#app')
