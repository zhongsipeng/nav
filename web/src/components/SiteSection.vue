<template>
    <div class="site-section">
        <!-- 加载中状态 -->
        <div v-if="loading" class="state-wrapper">
            <el-skeleton :rows="3" animated />
            <el-skeleton :rows="3" animated style="margin-top: 24px;" />
        </div>
        <!-- 空数据状态 -->
        <el-empty v-else-if="!sections || sections.length === 0" description="暂无书签数据" />
        <!-- 正常展示 -->
        <template v-else>
            <div v-for="(item, index) in sections" :key="index" class="section-block">
                <div v-if="index > 0" class="section-parent">
                    <el-tag
                        v-if="item.parentLabel"
                        size="small"
                        type="info"
                        effect="plain"
                        class="parent-tag"
                    >
                        {{ item.parentLabel }}
                    </el-tag>
                </div>
                <div class="section-header">
                    <el-icon class="section-icon">
                        <Folder />
                    </el-icon>
                    <span class="section-title">{{ item.label }}</span>
                </div>
                <el-row class="site-list" justify="start">
                    <el-card
                        v-for="site in item.children"
                        :key="site.id"
                        class="site-card"
                        shadow="hover"
                        @click="handleSiteClick(site)"
                    >
                        <el-row type="flex" :align="'middle'" justify="center">
                            <el-col :span="6">
                                <img :src="site.icon || appConfig.LOGO_URL" class="site-icon" />
                            </el-col>
                            <el-col :span="16" class="site-info">
                                <el-text tag="b" line-clamp="1" class="site-label">
                                    {{ site.label }}
                                </el-text>
                            </el-col>
                            <el-col :span="2">
                                <el-icon class="site-arrow">
                                    <ArrowRight />
                                </el-icon>
                            </el-col>
                        </el-row>
                    </el-card>
                </el-row>
            </div>
        </template>
    </div>
</template>

<script lang="ts" setup>
import { Folder, ArrowRight } from '@element-plus/icons-vue'
import { appConfig } from '@/config/appConfig'

interface SiteItem {
    id: number | null
    pid: number | null
    label: string
    icon?: string
    url?: string
    type: string
    children?: SiteItem[]
    [key: string]: any
}

interface SectionItem {
    parentLabel: string
    label: string
    children: SiteItem[]
}

const props = defineProps<{
    sections: SectionItem[]
    loading?: boolean
}>()

const emit = defineEmits<{
    (e: 'site-click', site: SiteItem): void
}>()

const handleSiteClick = (site: SiteItem) => {
    emit('site-click', site)
}
</script>

<style scoped>
.site-section {
    width: 100%;
}

.state-wrapper {
    padding: 20px 0;
}

.section-block {
    margin-bottom: 16px;
}

.section-block:last-child {
    margin-bottom: 0;
}

.section-parent {
    display: flex;
    align-items: center;
    margin-bottom: 4px;
}

.parent-tag {
    font-size: 12px;
}

.section-header {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    padding-left: 2px;
}

.section-icon {
    font-size: 18px;
    color: var(--el-color-primary);
    margin-right: 8px;
}

.section-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);
}

.site-list {
    gap: 12px;
    --el-row-gutter: 12px;
}

.site-card {
    width: 250px;
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.site-card:hover {
    transform: translateY(-2px);
}

.site-icon {
    width: 32px;
    height: 32px;
}

.site-info {
    cursor: pointer;
}

.site-label {
    max-width: 140px;
}

.site-arrow {
    color: var(--el-text-color-placeholder);
}
</style>
