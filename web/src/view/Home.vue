<template>
  <el-container>
    <el-aside class="content-wrapper" :width="isCollapse ? '64px' : '300px'">
      <el-row style="height: 80px;" type="flex" :align="'middle'" justify="center">
        <img :src="logoUrl" class="sidebar-logo" style="width: 64px; height: 64px;" />
      </el-row>
      <CollectTree :data="treedata" :collapse="isCollapse" @click="clickTree" @update="updateData"
        @dropupdate="handleDropUpdate" @toggle-collapse="isCollapse = !isCollapse"></CollectTree>
    </el-aside>

    <el-container>

      <el-header>
        <el-row type="flex" :align="'middle'" justify="left"
          style="max-height: 70px; border-bottom: 1px solid var(--el-menu-border-color)">
          <el-col :style="{ flex: '0 0 60px', minWidth: '60px' }">
            <div class="collapse-btn" @click="isCollapse = !isCollapse" style="text-align: center; cursor: pointer">
              <svg viewBox="0 0 100 100">
                <path class="line--1" d="M0 40h62c18 0 18-20-17 5L31 55"
                  :style='{ "--length": !isCollapse ? 12.602325267 : "" }'></path>
                <path class="line--2" d="M0 50h80"></path>
                <path class="line--3" d="M0 60h62c18 0 18 20-17-5L31 45"
                  :style='{ "--length": !isCollapse ? 12.602325267 : "" }'></path>
              </svg>
            </div>
          </el-col>
          <el-col :span="12">
            <el-menu style="border-bottom: 0px;" :default-active="1" class="el-menu-demo" mode="horizontal" @select="">

              <el-menu-item index="1">首页</el-menu-item>
              <!-- <el-menu-item index="2">收藏夹</el-menu-item>
              <el-menu-item index="3">常用</el-menu-item> -->
            </el-menu>
          </el-col>
          <el-col :span="8" style="text-align: right">
            <el-space>
              <el-upload ref="uploadRef" :show-file-list="false" :auto-upload="false" :on-change="handleFileChange"
                :limit="1" accept=".html,.htm">
                <el-button type="primary" :loading="importLoading">导入书签</el-button>
              </el-upload>
              <el-button type="success" @click="handleExport">导出书签</el-button>
            </el-space>
          </el-col>
        </el-row>

      </el-header>

      <el-main>

        <div class="m-large">
          <el-row class="row-bg" justify="center">
            <SearchC></SearchC>

          </el-row>
        </div>
        <el-row class="row-bg" justify="space-evenly">
          <div class="m-middle" style="width: 1500px;">
            <SiteSection :sections="sitelist" :loading="loading" @site-click="handleSiteClick" />
          </div>
        </el-row>
      </el-main>

      <el-footer>
        <!-- <el-pagination v-model:current-page="searchParams.page" v-model:page-size="searchParams.rows" :page-sizes="page"
        :size="size" :disabled="disabled" :background="background" layout="sizes, prev, pager, next, jumper"
        :total="total" @size-change="handleSizeChange" @current-change="handleCurrentChange" /> -->
      </el-footer>

    </el-container>
  </el-container>
</template>

<script lang="ts" setup>
import { onMounted, ref } from 'vue'
import CollectTree from '@/components/CollectTree.vue'
import getCollect, { delCollect, saveCollect, importCollect } from '@/api/collect'
import { customConfirm, successTip, errorTip } from '@/utils/tip'
import SearchC from '@/components/SearchC.vue'
import SiteSection from '@/components/SiteSection.vue'
import { appConfig } from '@/config/appConfig'


const isCollapse = ref(false) // 控制侧边栏是否收起
const importLoading = ref(false)
const loading = ref(false) // 数据加载状态
const uploadRef = ref(null) // el-upload 实例引用，用于清空内部文件列表
// 使用运行时动态绑定，避免 Vue 编译期把 public 静态资源当成可打包 module 处理
// （否则浏览器按 module script 解析 image/x-icon，报 MIME 类型错误）
const logoUrl = `${appConfig.LOGO_URL}`

const treedata = ref([])
const sitelist = ref([])

let nodeMapping = {}

// 递归遍历树结构，构建节点映射关系
function traverseTreeRecursive(node: any) {
  nodeMapping[node.id] = node
  Array.isArray(node.children) && node.children.forEach((child: any) => {
    traverseTreeRecursive(child)
  })
}
const getData = async () => {
  loading.value = true
  try {
    const res = await getCollect()
    treedata.value = res.data
    nodeMapping = {}
    treedata.value.forEach(x => {
      traverseTreeRecursive(x)

    })
    console.log(nodeMapping)
    // 数据加载完成后，自动展示第一个根节点的数据
    if (treedata.value && treedata.value.length > 0) {
      nodeMapping[treedata.value[0]["pid"]] = {
        id: treedata.value[0]["pid"],
        children: treedata.value,
        type: "folder"
      }
      clickTree(treedata.value[0])
    }
  } catch (e) {
    console.log(e)
    errorTip('数据加载失败')
  } finally {
    loading.value = false
  }
}
getData()
const clickTree = (node) => {
  if (node.type !== "folder") {
    window.open(node.url)
  } else {
    // 遍历node树形结构，把所有type等于"folder"的节点都添加到sitelist.value中
    sitelist.value = []
    const traverseFolders = (n) => {
      if (!n) return
      if (n.type === 'folder') {
        sitelist.value.push({ label: n.label, children: n.children.filter((x) => x.type !== 'folder'), parentLabel: nodeMapping[n.pid]?.label || '' })
      }
      if (n.children && n.children.length > 0) {
        n.children.forEach((child) => traverseFolders(child))
      }
    }
    traverseFolders(node)

  }
}

const handleSiteClick = (site) => {
  clickTree(site)
}
const handleDropUpdate = (node) => {
  clickTree(node)
}

const updateData = (lx, node) => {
  switch (lx) {
    case 'edit': case 'add':
      if (node.id === null) {
        saveCollect(node).then((res) => {
          nodeMapping[res.data.pid].children.push(res.data)
          nodeMapping[res.data.id] = nodeMapping[res.data.pid].children[nodeMapping[res.data.pid].children.length - 1]
          successTip(res.message)
          clickTree(nodeMapping[node.pid])
        })
        break
      } else {
        saveCollect(node).then((res) => {
          let treenode = nodeMapping[res.data.id]
          for (var key in res.data) {
            treenode[key] = res.data[key]
          }
          successTip(res.message)
          clickTree(nodeMapping[node.pid])

        })
      }
      break
    case 'del':
      customConfirm("确认删除？").then(() => {
        delCollect({ ids: [node.id] }).then((res) => {
          let index = nodeMapping[node.pid].children.findIndex((x) => x.id === node.id)
          nodeMapping[node.pid].children.splice(index, 1)
          successTip(res.message)
          clickTree(nodeMapping[node.pid])

        })

      })
      break
    default:
  }

}

// ===== 书签导入/导出 =====
const handleFileChange = async (file) => {
  try {
    if (!file || !file.raw) return

    // 文件类型校验
    const name = file.name.toLowerCase()
    if (!name.endsWith('.html') && !name.endsWith('.htm')) {
      errorTip('仅支持 .html 或 .htm 书签文件')
      return
    }
    // 文件大小校验 (10MB)
    if (file.size > appConfig.MAX_UPLOAD_SIZE) {
      errorTip('文件大小不能超过 10MB')
      return
    }
    // 确认清空现有数据
    try {
      await customConfirm('导入将清空现有书签数据，确认继续？')
    } catch {
      return
    }

    importLoading.value = true
    try {
      const res = await importCollect(file.raw)
      successTip(res.message)
      getData()
    } catch (e) {
      errorTip(e.message || '导入失败')
    } finally {
      importLoading.value = false
    }
  } finally {
    // 无论成功/失败/取消/校验不通过，都清空 el-upload 内部文件列表。
    // 否则 :limit="1" 会导致下一次选择文件不触发 on-change（不弹窗）。
    uploadRef.value?.clearFiles()
  }
}

const handleExport = () => {
  // 直接在新窗口打开导出接口，浏览器自动触发文件下载
  // 使用 API_BASE_URL 拼接保证与 axios 请求路径一致
  const exportUrl = appConfig.API_URLS.EXPORT_COLLECT
  const win = window.open(exportUrl, '_blank')
  if (!win) {
    errorTip('新窗口被浏览器拦截，请允许弹窗后重试')
    return
  }
  successTip('文件已导出')
}

</script>
<style scoped>
/* .search {
  background-color: antiquewhite;
} */
.round-boder {
  border: 1px solid var(--el-menu-border-color)
}

.content-wrapper {
  transition: width 0.2s ease;
  /* 水平动画 */
  overflow: hidden;
  /* 隐藏溢出内容 */
}

.collapse-btn .line--1,
.collapse-btn .line--3 {
  --total-length: 126.38166809082031;
}

.collapse-btn .line--2 {
  --total-length: 80;
}

.collapse-btn path {
  fill: none;
  stroke: #888;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
  --length: 24;
  --offset: -38;
  stroke-dasharray: var(--length) var(--total-length);
  stroke-dashoffset: var(--offset);

  transition: all .5s cubic-bezier(.645, .045, .355, 1), stroke .2s ease;
}
</style>
