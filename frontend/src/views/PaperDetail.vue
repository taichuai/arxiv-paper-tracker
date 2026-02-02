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

      <!-- 机构信息（高亮显示头部机构） -->
      <div v-if="paper.affiliations && paper.affiliations.length > 0" class="mb-4">
        <strong class="text-gray-600">机构:</strong>
        <div class="flex flex-wrap gap-2 mt-2">
          <span
            v-for="(aff, index) in paper.affiliations"
            :key="index"
            :class="[
              'px-3 py-1 rounded-full text-sm',
              isTopInstitution(aff)
                ? 'bg-gradient-to-r from-amber-400 to-orange-500 text-white font-semibold shadow'
                : 'bg-gray-100 text-gray-700'
            ]"
          >
            {{ aff }}
          </span>
        </div>
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

      <div class="flex flex-wrap gap-4 mt-6">
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
          arXiv
        </a>
        <a
          :href="getAlphaXivUrl(paper.arxiv_id)"
          target="_blank"
          class="flex-1 px-6 py-3 bg-purple-600 text-white text-center rounded-lg hover:bg-purple-700"
        >
          AlphaXiv
        </a>
        <a
          v-if="paper.github_url"
          :href="paper.github_url"
          target="_blank"
          class="flex-1 px-6 py-3 bg-gray-800 text-white text-center rounded-lg hover:bg-gray-900 flex items-center justify-center gap-2"
        >
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
          </svg>
          GitHub
        </a>
      </div>

      <!-- BibTeX 复制按钮 -->
      <div class="mt-4">
        <button
          @click="copyBibtex"
          class="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"/>
          </svg>
          复制 BibTeX 引用
        </button>
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
      loading: false,
      // 从后端配置加载
      topInstitutions: []
    }
  },
  mounted() {
    this.loadConfig()
    this.loadPaper()
  },
  methods: {
    async loadConfig() {
      try {
        const response = await axios.get('/api/config/')
        this.topInstitutions = response.data.top_institutions || []
      } catch (error) {
        console.error('加载配置失败:', error)
      }
    },
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
    },
    getAlphaXivUrl(arxivId) {
      // arXiv ID 格式: 2601.23255 -> https://www.alphaxiv.org/abs/2601.23255
      return `https://www.alphaxiv.org/abs/${arxivId}`
    },
    isTopInstitution(affiliation) {
      if (!affiliation) return false
      const lower = affiliation.toLowerCase()
      return this.topInstitutions.some(inst => lower.includes(inst.toLowerCase()))
    },
    async copyBibtex() {
      try {
        const response = await axios.get(`/api/papers/${this.id}/bibtex`)
        await navigator.clipboard.writeText(response.data)
        alert('BibTeX 已复制到剪贴板')
      } catch (error) {
        console.error('复制 BibTeX 失败:', error)
        alert('复制失败')
      }
    }
  }
}
</script>
