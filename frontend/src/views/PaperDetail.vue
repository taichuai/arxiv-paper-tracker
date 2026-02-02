<template>
  <div>
    <button
      @click="$router.back()"
      class="mb-4 text-blue-600 hover:underline"
    >
      ← 返回列表
    </button>

    <div v-if="loading" class="text-center py-12">
      <div class="text-gray-500">加载中...</div>
    </div>

    <div v-else-if="paper" class="bg-white p-8 rounded-lg shadow">
      <div class="flex items-start justify-between mb-4">
        <h1 class="text-3xl font-bold text-gray-900 flex-1 mr-4">
          {{ paper.title }}
        </h1>
        <button
          @click="toggleBookmark"
          class="text-3xl"
        >
          {{ paper.is_bookmarked ? '⭐' : '☆' }}
        </button>
      </div>

      <div class="text-gray-600 mb-4">
        <strong>作者:</strong> {{ paper.authors }}
      </div>

      <div class="flex flex-wrap gap-2 mb-6">
        <span
          v-if="paper.subcategory"
          class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full"
        >
          {{ paper.subcategory }}
        </span>
        <span
          v-if="paper.relevance_score"
          class="px-3 py-1 bg-green-100 text-green-800 rounded-full"
        >
          相关性评分: {{ paper.relevance_score.toFixed(1) }} / 10
        </span>
      </div>

      <div v-if="paper.chinese_summary" class="mb-6">
        <h2 class="text-xl font-semibold mb-2">中文摘要</h2>
        <p class="text-gray-700 leading-relaxed">{{ paper.chinese_summary }}</p>
      </div>

      <div class="mb-6">
        <h2 class="text-xl font-semibold mb-2">原文摘要</h2>
        <p class="text-gray-700 leading-relaxed">{{ paper.abstract }}</p>
      </div>

      <div v-if="paper.keywords && paper.keywords.length > 0" class="mb-6">
        <h2 class="text-xl font-semibold mb-2">关键词</h2>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="keyword in paper.keywords"
            :key="keyword"
            class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full"
          >
            {{ keyword }}
          </span>
        </div>
      </div>

      <div class="border-t pt-6 mt-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <strong>发布日期:</strong> {{ formatDate(paper.published_date) }}
          </div>
          <div>
            <strong>arXiv ID:</strong> {{ paper.arxiv_id }}
          </div>
          <div>
            <strong>分类:</strong> {{ paper.categories }}
          </div>
        </div>
      </div>

      <div class="flex gap-4 mt-6">
        <a
          :href="paper.pdf_url"
          target="_blank"
          class="flex-1 px-6 py-3 bg-blue-600 text-white text-center rounded-lg hover:bg-blue-700"
        >
          查看 PDF
        </a>
        <a
          :href="paper.arxiv_url"
          target="_blank"
          class="flex-1 px-6 py-3 bg-gray-200 text-gray-800 text-center rounded-lg hover:bg-gray-300"
        >
          在 arXiv 上查看
        </a>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import dayjs from 'dayjs'

export default {
  name: 'PaperDetail',
  props: {
    id: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      paper: null,
      loading: false
    }
  },
  mounted() {
    this.loadPaper()
  },
  methods: {
    async loadPaper() {
      this.loading = true
      try {
        const response = await axios.get(`/api/papers/${this.id}`)
        this.paper = response.data

        // 标记为已读
        await axios.post(`/api/papers/${this.id}/read`)
      } catch (error) {
        console.error('加载论文失败:', error)
        alert('加载失败')
      } finally {
        this.loading = false
      }
    },
    async toggleBookmark() {
      try {
        const response = await axios.post(`/api/papers/${this.id}/bookmark`)
        this.paper.is_bookmarked = response.data.bookmarked
      } catch (error) {
        console.error('收藏失败:', error)
      }
    },
    formatDate(date) {
      return dayjs(date).format('YYYY-MM-DD HH:mm')
    }
  }
}
</script>
