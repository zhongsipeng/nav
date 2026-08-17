<script setup lang="ts">
import { useRoute } from 'vue-router'
import { Menu as IconMenu, List, Search } from '@element-plus/icons-vue'


// defineProps({
//   current: {
//     type: String,
//     // required: true,
//   },
// })
const route = useRoute()
const lastMatched = route.matched[route.matched.length - 1]
const lastSegmentFromMatched = lastMatched.path.split('/').pop()
const ICONBus = {
  "List": List
}
</script>
<template>

  <el-menu router :default-active="lastSegmentFromMatched">
    <el-sub-menu
      v-for='(item, index) in [{ "id": "4", "title": "菜单", "icon": "List", "chiren": [{ "id": "11", "title": "游戏数据", "route": "home" }, { "id": "12", "title": "搜索", "route": "home" }] }]'
      :index="item.id">
      <template #title>
        <el-icon>
          <component :is="ICONBus[item.icon]"></component>
          <!-- <List /> -->
        </el-icon> {{ item.title }}
      </template>
      <el-menu-item @click="console.log" v-for="(child, cindex) in item.chiren" :index="child.route">{{ child.title
      }}</el-menu-item>
    </el-sub-menu>
  </el-menu>

</template>