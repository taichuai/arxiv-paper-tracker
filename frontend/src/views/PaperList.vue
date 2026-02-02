<template>
  <div>
    <!-- 本周精选 -->
    <div v-if="featuredPapers.length > 0" class="mb-8">
      <div class="flex items-center gap-2 mb-4">
        <span class="text-2xl">&#11088;</span>
        <h2 class="text-xl font-bold text-gray-900">本周精选</h2>
        <span class="text-sm text-gray-500">创新性最高的 {{ featuredPapers.length }} 篇论文</span>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="paper in featuredPapers"
          :key="'featured-' + paper.id"
          @click="goToDetail(paper.id)"
          class="bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 p-4 rounded-xl shadow-md hover:shadow-xl transition-all cursor-pointer"
        >
          <div class="flex items-start justify-between mb-2">
            <h3 class="font-semibold text-gray-900 line-clamp-2 flex-1 mr-2 text-sm">
              {{ paper.title }}
            </h3>
            <span class="flex-shrink-0 px-2 py-1 bg-gradient-to-r from-amber-400 to-orange-500 text-white text-xs font-bold rounded-full">
              {{ paper.innovation_score?.toFixed(1) }}
            </span>
          </div>
          <div class="text-xs text-gray-500 mb-2 line-clamp-1">
            {{ paper.authors }}
          </div>
          <div v-if="paper.affiliations && paper.affiliations.length > 0" class="flex flex-wrap gap-1 mb-2">
            <span
              v-for="(aff, index) in paper.affiliations.slice(0, 2)"
              :key="index"
              :class="[
                'text-xs px-1.5 py-0.5 rounded',
                isTopInstitution(aff)
                  ? 'bg-amber-500 text-white font-medium'
                  : 'bg-gray-200 text-gray-600'
              ]"
            >
              {{ aff }}
            </span>
          </div>
          <div class="text-xs text-gray-600 line-clamp-2 mb-2">
            {{ paper.chinese_summary }}
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
              {{ paper.subcategory }}
            </span>
            <span class="text-xs text-gray-400">
              {{ formatDate(paper.published_date) }}
            </span>
          </div>
          <div v-if="paper.innovation_reason" class="mt-2 text-xs text-amber-700 italic line-clamp-1">
            &#128161; {{ paper.innovation_reason }}
          </div>
        </div>
      </div>
    </div>

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
      <!-- 搜索框 -->
      <div class="mb-4">
        <div class="flex gap-2">
          <input
            v-model="searchQuery"
            @keyup.enter="doSearch"
            type="text"
            placeholder="搜索论文标题、摘要、作者..."
            class="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <button
            @click="doSearch"
            class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            搜索
          </button>
          <button
            v-if="isSearchMode"
            @click="clearSearch"
            class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
          >
            清除
          </button>
        </div>
      </div>

      <!-- 高级筛选（可折叠） -->
      <div class="mb-4">
        <button
          @click="showAdvancedFilters = !showAdvancedFilters"
          class="text-sm text-blue-600 hover:underline flex items-center gap-1"
        >
          <span>{{ showAdvancedFilters ? '收起' : '展开' }}高级筛选</span>
          <svg :class="['w-4 h-4 transition-transform', showAdvancedFilters ? 'rotate-180' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
          </svg>
        </button>

        <div v-show="showAdvancedFilters" class="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <label class="block text-xs text-gray-500 mb-1">机构筛选</label>
            <input
              v-model="advancedFilters.institution"
              type="text"
              placeholder="如: Google, MIT"
              class="w-full px-3 py-2 border rounded-lg text-sm"
            />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">最低评分</label>
            <input
              v-model.number="advancedFilters.minScore"
              type="number"
              min="0"
              max="10"
              step="0.5"
              placeholder="0-10"
              class="w-full px-3 py-2 border rounded-lg text-sm"
            />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">开始日期</label>
            <input
              v-model="advancedFilters.dateFrom"
              type="date"
              class="w-full px-3 py-2 border rounded-lg text-sm"
            />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">结束日期</label>
            <input
              v-model="advancedFilters.dateTo"
              type="date"
              class="w-full px-3 py-2 border rounded-lg text-sm"
            />
          </div>
          <div class="col-span-2 md:col-span-4 flex items-center gap-4">
            <label class="flex items-center gap-2 text-sm">
              <input type="checkbox" v-model="advancedFilters.hasGithub" class="rounded">
              <span>仅有代码</span>
            </label>
            <button
              @click="applyAdvancedFilters"
              class="px-4 py-1.5 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 text-sm"
            >
              应用筛选
            </button>
            <button
              @click="resetAdvancedFilters"
              class="px-4 py-1.5 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 text-sm"
            >
              重置
            </button>
          </div>
        </div>
      </div>

      <!-- 基础筛选 -->
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

        <!-- BibTeX 导出按钮 -->
        <button
          @click="exportBookmarkedBibtex"
          class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-1"
          title="导出所有收藏论文的 BibTeX"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          导出 BibTeX
        </button>
      </div>
    </div>

    <!-- 搜索结果提示 -->
    <div v-if="isSearchMode" class="mb-4 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg flex items-center justify-between">
      <span>搜索 "{{ lastSearchQuery }}" 找到 {{ total }} 条结果</span>
      <button @click="clearSearch" class="text-blue-600 hover:underline text-sm">返回全部</button>
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

        <!-- 机构信息 -->
        <div v-if="paper.affiliations && paper.affiliations.length > 0" class="mb-2 flex flex-wrap items-center gap-1">
          <svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
          </svg>
          <template v-for="(aff, index) in paper.affiliations.slice(0, 3)" :key="index">
            <span
              :class="[
                'text-xs px-2 py-0.5 rounded',
                isTopInstitution(aff)
                  ? 'bg-gradient-to-r from-amber-400 to-orange-500 text-white font-semibold shadow-sm'
                  : 'bg-gray-100 text-gray-600'
              ]"
            >
              {{ aff }}
            </span>
          </template>
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
              v-if="paper.github_url"
              :href="paper.github_url"
              target="_blank"
              @click.stop
              class="text-gray-700 hover:text-black flex items-center gap-1"
              title="查看代码"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              Code
            </a>
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
            <button
              @click.stop="copyBibtex(paper.id)"
              class="text-gray-500 hover:text-gray-700"
              title="复制 BibTeX"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"/>
              </svg>
            </button>
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
      featuredPapers: [],
      stats: null,
      loading: false,
      page: 1,
      pageSize: 20,
      total: 0,
      // 搜索相关
      searchQuery: '',
      lastSearchQuery: '',
      isSearchMode: false,
      showAdvancedFilters: false,
      advancedFilters: {
        institution: '',
        minScore: null,
        dateFrom: '',
        dateTo: '',
        hasGithub: false
      },
      filters: {
        sortBy: 'date_desc',
        subcategory: '',
        bookmarkedOnly: false,
        days: null
      },
      // 从后端配置加载
      subcategories: [],
      topInstitutions: []
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
    this.loadConfig()  // 先加载配置
    this.loadPapers()
    this.loadStats()
    this.loadFeaturedPapers()
  },
  methods: {
    async loadConfig() {
      try {
        const response = await axios.get('/api/config/')
        this.topInstitutions = response.data.top_institutions || []
        this.subcategories = response.data.subcategories || []
      } catch (error) {
        console.error('加载配置失败:', error)
        // 使用默认值
        this.subcategories = [
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
    async loadFeaturedPapers() {
      try {
        const response = await axios.get('/api/papers/featured/weekly')
        this.featuredPapers = response.data
      } catch (error) {
        console.error('加载精选论文失败:', error)
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
    },
    isTopInstitution(affiliation) {
      if (!affiliation) return false
      const lower = affiliation.toLowerCase()
      return this.topInstitutions.some(inst => lower.includes(inst.toLowerCase()))
    },

    // 搜索相关方法
    async doSearch() {
      if (!this.searchQuery.trim()) {
        this.clearSearch()
        return
      }

      this.loading = true
      this.isSearchMode = true
      this.lastSearchQuery = this.searchQuery
      this.page = 1

      try {
        const params = {
          q: this.searchQuery,
          page: this.page,
          page_size: this.pageSize,
          sort_by: this.filters.sortBy
        }

        // 添加高级筛选参数
        if (this.advancedFilters.institution) {
          params.institution = this.advancedFilters.institution
        }
        if (this.advancedFilters.minScore) {
          params.min_score = this.advancedFilters.minScore
        }
        if (this.advancedFilters.dateFrom) {
          params.date_from = this.advancedFilters.dateFrom
        }
        if (this.advancedFilters.dateTo) {
          params.date_to = this.advancedFilters.dateTo
        }
        if (this.advancedFilters.hasGithub) {
          params.has_github = true
        }
        if (this.filters.subcategory) {
          params.subcategory = this.filters.subcategory
        }
        if (this.filters.bookmarkedOnly) {
          params.bookmarked_only = true
        }

        const response = await axios.get('/api/papers/search', { params })
        this.papers = response.data.papers
        this.total = response.data.total
      } catch (error) {
        console.error('搜索失败:', error)
        alert('搜索失败')
      } finally {
        this.loading = false
      }
    },

    clearSearch() {
      this.searchQuery = ''
      this.lastSearchQuery = ''
      this.isSearchMode = false
      this.resetAdvancedFilters()
      this.loadPapers()
    },

    applyAdvancedFilters() {
      this.doSearch()
    },

    resetAdvancedFilters() {
      this.advancedFilters = {
        institution: '',
        minScore: null,
        dateFrom: '',
        dateTo: '',
        hasGithub: false
      }
    },

    // BibTeX 相关方法
    async copyBibtex(paperId) {
      try {
        const response = await axios.get(`/api/papers/${paperId}/bibtex`)
        await navigator.clipboard.writeText(response.data)
        alert('BibTeX 已复制到剪贴板')
      } catch (error) {
        console.error('复制 BibTeX 失败:', error)
        alert('复制失败')
      }
    },

    async exportBookmarkedBibtex() {
      try {
        const response = await axios.get('/api/papers/export/bibtex', {
          params: { bookmarked_only: true }
        })

        // 创建下载
        const blob = new Blob([response.data], { type: 'text/plain' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'bookmarked_papers.bib'
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error('导出失败:', error)
        if (error.response?.status === 400) {
          alert('没有收藏的论文可导出')
        } else {
          alert('导出失败')
        }
      }
    }
  }
}
</script>
