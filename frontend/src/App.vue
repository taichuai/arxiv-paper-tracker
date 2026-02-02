<template>
  <div id="app">
    <header class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">arXiv Paper Tracker</h1>
            <p class="text-sm text-gray-500">语音方向论文追踪系统</p>
          </div>
          <div class="flex gap-2">
            <button
              @click="triggerFetch"
              :disabled="isFetching"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ isFetching ? '获取中...' : '立即获取论文' }}
            </button>
          </div>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <router-view @trigger-fetch="triggerFetch" />
    </main>

    <footer class="bg-white border-t mt-auto">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-center text-sm text-gray-500">
        © 2024 arXiv Paper Tracker | 基于 FastAPI + Vue 3 构建
      </div>
    </footer>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      isFetching: false
    }
  },
  methods: {
    async triggerFetch() {
      this.isFetching = true
      try {
        await axios.post('/api/tasks/fetch-now')
        alert('论文获取任务已启动！请等待几分钟后刷新页面查看新论文。')
      } catch (error) {
        console.error('触发获取失败:', error)
        alert('触发失败，请检查后端服务是否运行')
      } finally {
        this.isFetching = false
      }
    }
  }
}
</script>

<style>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
