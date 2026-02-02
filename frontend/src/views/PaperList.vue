<template>
  <div>
    <!-- 统计卡片 -->
    <div v-if="stats" class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white p-4 rounded-lg shadow">
        <div class="text-sm text-gray-500">总论文数</div>
        <div class="text-2xl font-bold">{{ stats.total_papers }}</div>
      </div>
      <div class="bg-white p-4 rounded-lg shadow">
        <div class="text-sm text-gray-500">已收藏</div>
        <div class="text-2xl font-bold text-yellow-600">{{ stats.total_bookmarked }}</div>
      </div>
      <div class="bg-white p-4 rounded-lg shadow">
        <div class="text-sm text-gray-500">最近7天</div>
        <div class="text-2xl font-bold text-blue-600">{{ stats.recent_papers }}</div>
      </div>
      <div class="bg-white p-4 rounded-lg shadow">
        <div class="text-sm text-gray-500">子领域</div>
        <div class="text-2xl font-bold">{{ Object.keys(stats.subcategory_distribution || {}).length }}</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="bg-white p-4 rounded-lg shadow mb-6">
      <div class="flex flex-wrap gap-4">
        <select v-model="filters.sortBy" class="px-3 py-2 border rounded-lg">
          <option value="date_desc">最新发布</option>
          <option value="date_asc">最早发布</option>
          <option value="relevance">相关性</option>
        </select>

        <select v-model="filters.subcategory" class="px-3 py-2 border rounded-lg">
          <option value="">所有分类</option>
          <option v-for="cat in subcategories" :key="cat" :value="cat">{{ cat }}</option>
        </select>

        <select v-model="filters.days" class="px-3 py-2 border rounded-lg">
          <option :value="null">全部时间</option>
          <option :value="1">今天</option>
          <option :value="7">最近7天</option>
          <option :value="30">最近30天</option>
        </select>

        <label class="flex items-center gap-2">
          <input type="checkbox" v-model="filters.bookmarkedOnly" class="rounded">
          <span>仅显示收藏</span>
        </label>

        <button
          @click="loadPapers"
          class="ml-auto px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
        >
          刷新
        </button>
      </div>
    </div>

    <!-- 论文列表 -->
    <div v-if="loading" class="text-center py-12">
      <div class="text-gray-500">加载中...</div>
    </div>

    <div v-else-if="papers.length === 0" class="bg-white p-12 rounded-lg shadow text-center">
      <div class="text-gray-500 mb-4">暂无论文</div>
      <button
        @click="$emit('trigger-fetch')"
        class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        立即获取论文
      </button>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="paper in papers"
        :key="paper.id"
        class="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer"
        @click="goToDetail(paper.id)"
      >
        <div class="flex items-start justify-between mb-2">
          <h3 class="text-lg font-semibold text-gray-900 flex-1 mr-4">
            {{ paper.title }}
          </h3>
          <button
            @click.stop="toggleBookmark(paper.id, paper.is_bookmarked)"
            class="text-2xl"
          >
            {{ paper.is_bookmarked ? '⭐' : '☆' }}
          </button>
        </div>

        <div class="text-sm text-gray-600 mb-2">
          {{ paper.authors }}
        </div>

        <div v-if="paper.chinese_summary" class="text-gray-700 mb-3">
          {{ paper.chinese_summary }}
        </div>

        <div class="flex flex-wrap gap-2 mb-3">
          <span
            v-if="paper.subcategory"
            class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
          >
            {{ paper.subcategory }}
          </span>
          <span
            v-if="paper.relevance_score"
            class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded"
          >
            相关性: {{ paper.relevance_score.toFixed(1) }}
          </span>
          <span
            v-for="keyword in (paper.keywords || []).slice(0, 5)"
            :key="keyword"
            class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
          >
            {{ keyword }}
          </span>
        </div>

        <div class="flex items-center justify-between text-sm text-gray-500">
          <div>{{ formatDate(paper.published_date) }}</div>
          <div class="flex gap-3">
            <a
              :href="paper.pdf_url"
              target="_blank"
              @click.stop
              class="text-blue-600 hover:underline"
            >
              PDF
            </a>
            <a
              :href="paper.arxiv_url"
              target="_blank"
              @click.stop
              class="text-blue-600 hover:underline"
            >
              arXiv
            </a>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="flex justify-center gap-2 mt-6">
        <button
          v-for="p in totalPages"
          :key="p"
          @click="changePage(p)"
          :class="[
            'px-4 py-2 rounded-lg',
            p === page ? 'bg-blue-600 text-white' : 'bg-white hover:bg-gray-100'
          ]"
        >
          {{ p }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

dayjs.locale('zh-cn')

export default {
  name: 'PaperList',
  data() {
    return {
      papers: [],
      stats: null,
      loading: false,
      page: 1,
      pageSize: 20,
      total: 0,
      filters: {
        sortBy: 'date_desc',
        subcategory: '',
        bookmarkedOnly: false,
        days: null
      },
      subcategories: [
        'TTS (语音合成)',
        'ASR (语音识别)',
        '语音增强',
        '说话人识别/验证',
        '语音转换',
        '歌声合成',
        '语音情感识别',
        '多模态语音',
        '其他'
      ]
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.total / this.pageSize)
    }
  },
  watch: {
    filters: {
      handler() {
        this.page = 1
        this.loadPapers()
      },
      deep: true
    }
  },
  mounted() {
    this.loadPapers()
    this.loadStats()
  },
  methods: {
    async loadPapers() {
      this.loading = true
      try {
        const params = {
          page: this.page,
          page_size: this.pageSize,
          sort_by: this.filters.sortBy
        }

        if (this.filters.subcategory) {
          params.subcategory = this.filters.subcategory
        }
        if (this.filters.bookmarkedOnly) {
          params.bookmarked_only = true
        }
        if (this.filters.days) {
          params.days = this.filters.days
        }

        const response = await axios.get('/api/papers/', { params })
        this.papers = response.data.papers
        this.total = response.data.total
      } catch (error) {
        console.error('加载论文失败:', error)
        alert('加载失败，请确保后端服务正在运行')
      } finally {
        this.loading = false
      }
    },
    async loadStats() {
      try {
        const response = await axios.get('/api/papers/stats/summary')
        this.stats = response.data
      } catch (error) {
        console.error('加载统计失败:', error)
      }
    },
    async toggleBookmark(paperId, currentState) {
      try {
        await axios.post(`/api/papers/${paperId}/bookmark`)
        // 更新本地状态
        const paper = this.papers.find(p => p.id === paperId)
        if (paper) {
          paper.is_bookmarked = !currentState
        }
        this.loadStats() // 更新统计
      } catch (error) {
        console.error('收藏失败:', error)
      }
    },
    changePage(p) {
      this.page = p
      this.loadPapers()
      window.scrollTo(0, 0)
    },
    goToDetail(paperId) {
      this.$router.push(`/paper/${paperId}`)
    },
    formatDate(date) {
      return dayjs(date).format('YYYY-MM-DD')
    }
  }
}
</script>
