<template>
  <el-container style="height: 100%">
    <el-aside width="200px">
      <el-scrollbar>
        <Menu></Menu>
      </el-scrollbar>
    </el-aside>
    <!-- 子路由内容将渲染在这里 -->
    <router-view v-slot="{ Component }">
      <keep-alive>
        <component :is="Component" />
      </keep-alive>
    </router-view>
  </el-container>
</template>
<script>
export default {
  data() {
    return {
      cachedViews: [] // 动态管理缓存
    }
  },
  watch: {
    $route() {
      if (this.$route.meta.keepAlive && !this.cachedViews.includes(this.$route.name)) {
        this.cachedViews.push(this.$route.name)
      }
    }
  }
}
</script>
<script setup>
import Menu from '@/components/Menu.vue'
</script>