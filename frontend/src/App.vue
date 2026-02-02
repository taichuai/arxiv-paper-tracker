<template>
  <div id="app">
    <!-- Toast 通知 -->
    <Transition name="toast">
      <div
        v-if="toast.show"
        :class="[
          'fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg max-w-md',
          toast.type === 'success' ? 'bg-green-500 text-white' : '',
          toast.type === 'error' ? 'bg-red-500 text-white' : '',
          toast.type === 'info' ? 'bg-blue-500 text-white' : ''
        ]"
      >
        <div class="flex items-center gap-3">
          <span v-if="toast.type === 'success'" class="text-xl">&#10003;</span>
          <span v-else-if="toast.type === 'error'" class="text-xl">&#10007;</span>
          <span v-else class="text-xl">&#8505;</span>
          <span>{{ toast.message }}</span>
        </div>
      </div>
    </Transition>

    <!-- 确认对话框 -->
    <Transition name="modal">
      <div v-if="confirmModal.show" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/50" @click="confirmModal.show = false"></div>
        <div class="relative bg-white rounded-xl shadow-2xl p-6 max-w-md mx-4">
          <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ confirmModal.title }}</h3>
          <p class="text-gray-600 mb-6">{{ confirmModal.message }}</p>
          <div class="flex gap-3 justify-end">
            <button
              @click="confirmModal.show = false"
              class="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              取消
            </button>
            <button
              @click="handleConfirm"
              class="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              继续刷新
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <header class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">arXiv Paper Tracker</h1>
            <p class="text-sm text-gray-500">
              语音方向论文追踪系统
              <span v-if="lastFetchTime" class="ml-2 text-gray-400">
                | 上次刷新: {{ formatTime(lastFetchTime) }}
              </span>
            </p>
          </div>
          <div class="flex gap-2">
            <button
              @click="handleFetchClick"
              :disabled="isFetching"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <svg v-if="isFetching" class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
              {{ isFetching ? '获取中...' : '立即获取论文' }}
            </button>
          </div>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <router-view ref="paperList" @trigger-fetch="handleFetchClick" />
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

// 刷新间隔阈值（毫秒）- 30分钟内再次刷新会提示
const FETCH_INTERVAL_THRESHOLD = 30 * 60 * 1000

export default {
  name: 'App',
  data() {
    return {
      isFetching: false,
      lastFetchTime: null,
      toast: {
        show: false,
        message: '',
        type: 'info'
      },
      confirmModal: {
        show: false,
        title: '',
        message: ''
      }
    }
  },
  mounted() {
    // 从 localStorage 读取上次刷新时间
    const saved = localStorage.getItem('lastFetchTime')
    if (saved) {
      this.lastFetchTime = new Date(saved)
    }
  },
  methods: {
    showToast(message, type = 'info', duration = 4000) {
      this.toast = { show: true, message, type }
      setTimeout(() => {
        this.toast.show = false
      }, duration)
    },
    formatTime(date) {
      if (!date) return ''
      const d = new Date(date)
      const now = new Date()
      const diff = now - d

      // 小于1分钟
      if (diff < 60 * 1000) {
        return '刚刚'
      }
      // 小于1小时
      if (diff < 60 * 60 * 1000) {
        return `${Math.floor(diff / 60000)} 分钟前`
      }
      // 小于24小时
      if (diff < 24 * 60 * 60 * 1000) {
        return `${Math.floor(diff / 3600000)} 小时前`
      }
      // 超过24小时显示日期
      return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
    },
    handleFetchClick() {
      // 检查是否在阈值时间内已刷新过
      if (this.lastFetchTime) {
        const timeSinceLastFetch = Date.now() - new Date(this.lastFetchTime).getTime()
        if (timeSinceLastFetch < FETCH_INTERVAL_THRESHOLD) {
          const minutesAgo = Math.floor(timeSinceLastFetch / 60000)
          this.confirmModal = {
            show: true,
            title: '确认刷新',
            message: `您在 ${minutesAgo} 分钟前刚刷新过数据。再次刷新会消耗 API Token，且可能没有新论文。确定要继续吗？`
          }
          return
        }
      }
      // 超过阈值或首次刷新，直接执行
      this.triggerFetch()
    },
    handleConfirm() {
      this.confirmModal.show = false
      this.triggerFetch()
    },
    async triggerFetch() {
      this.isFetching = true
      this.showToast('正在获取论文，请稍候...', 'info')

      try {
        const response = await axios.post('/api/tasks/fetch-now')
        const data = response.data

        if (data.success) {
          // 记录刷新时间
          this.lastFetchTime = new Date()
          localStorage.setItem('lastFetchTime', this.lastFetchTime.toISOString())

          if (data.new_papers > 0) {
            this.showToast(`获取成功！新增 ${data.new_papers} 篇论文`, 'success', 5000)
          } else {
            this.showToast('没有发现新论文', 'info')
          }

          // 自动刷新列表
          this.refreshPaperList()
        } else {
          this.showToast(data.message || '获取失败', 'error')
        }
      } catch (error) {
        console.error('触发获取失败:', error)
        this.showToast('获取失败，请检查后端服务是否运行', 'error')
      } finally {
        this.isFetching = false
      }
    },
    refreshPaperList() {
      // 调用子组件的刷新方法
      if (this.$refs.paperList && this.$refs.paperList.loadPapers) {
        this.$refs.paperList.loadPapers()
        this.$refs.paperList.loadStats()
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

/* Toast 动画 */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* Modal 动画 */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .relative,
.modal-leave-to .relative {
  transform: scale(0.9);
}
</style>
