<template>
    <div>


        <div>

            <el-dropdown class="height-adjusted-dropdown" @command="handleCommand" size="large">
                <span class="el-dropdown-link">
                    {{ menuText }}<el-icon class="el-icon--right"><arrow-down /></el-icon>
                </span>

                <template #dropdown>
                    <el-dropdown-menu>
                        <el-dropdown-item v-for="(value, index) in menuOption" :command="index">
                            {{ value.name }}
                        </el-dropdown-item>
                    </el-dropdown-menu>
                </template>
            </el-dropdown>
            <el-segmented v-model="searchOptionValue" :options="searchOption" size="large" />

        </div>
        <div class="search">
            <el-space wrap>
                <el-input v-model="searchText" class="search-input" clearable
                    placeholder="请输入搜索内容" @change="">
                    <template #append>
                        <el-button @click="serach" :icon="Search" />
                    </template>
                </el-input>
            </el-space>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { Search, Plus, Refresh, ArrowRight, Expand, Fold, Folder, ArrowDown } from '@element-plus/icons-vue'



import { nextTick, PropType, reactive, ref, watch } from 'vue'
import { customConfirm, successTip } from '@/utils/tip'
const searchText = ref("")
const handleCommand = (command) => {
    menuText.value = menuOption[command].name
    // console.log(command)
}
const menuText = ref("")
const menuOption = [
    {
        "name": "常用",
        "id": "1",
    },
    // {
    //     "name": "其他",
    //     "id": "2",
    // }
]
menuText.value = menuOption.length > 0 ? menuOption[0].name : "-"
const searchOption = [
    {
        "label": "必应",
        "value": "https://www.bing.com/search?q={searchText}"
    },
    {
        "label": "谷歌",
        "value": "https://www.google.com/search?q={searchText}"
    },
    // {
    //     "label": "yandex",
    //     "value": "https://yandex.com/"
    // },
    {
        "label": "百度",
        "value": "https://www.baidu.com/s?wd={searchText}"
    },
]
const searchOptionValue = ref(searchOption[0].value)
const serach = () => {
    window.open(searchOptionValue.value.replace("{searchText}", searchText.value))

}

</script>
<style>
/* .search input:focus {
    outline: none;
    /* 移除默认边框 */
/* margin: var(--small); 
 
*/
.el-segmented {
    --el-segmented-item-selected-color: #ffffff;
    --el-segmented-item-selected-bg-color: var(-l-color-primary);
    --el-segmented-padding: none;
    /* --el-border-radius-base: 16px; */
}

.search .is-focus {
    outline: none;
    box-shadow: 0 0 0 1px var(--el-input-border-color, var(--el-border-color)) inset;
    /* 或者你想要的任何颜色 */
}

.height-adjusted-dropdown {
    height: 40px;
    /* 与 el-segmented 高度一致 */
}

.el-dropdown-link {
    height: 100%;
    display: flex;
    align-items: center;
    padding: 0 15px;
    font-size: 14px;
    /* border: 1px solid #DCDFE6; */
    /* border-radius: 4px; */
    background: white;
}

.height-adjusted-dropdown .el-dropdown-link:focus {
    outline: none;
    box-shadow: none;
}

/* ===== 大搜索框样式 ===== */
.search {
    display: flex;
    justify-content: center;
    padding: 24px 0 16px;
    width: 700px;
}

.search .el-space {
    width: 100%;
    max-width: 900px;
}

.search .el-space__item {
    width: 100%;
}

/* 整体胶囊容器：宽度 + 圆角 + 阴影 + 边框 */
.search .el-input.search-input {
    width: 100%;
    border-radius: 32px;
    overflow: hidden;
    border: 1px solid var(--el-border-color, #dcdfe6);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
}

/* Hover 状态：边框加深 */
.search .el-input.search-input:hover {
    border-color: var(--el-border-color-hover, #c0c4cc);
}

/* Focus 状态：主题色边框 + 光晕 */
.search .el-input.search-input:focus-within {
    border-color: var(--el-color-primary, #409eff);
    box-shadow: 0 8px 24px rgba(64, 158, 255, 0.18);
}

/* Disabled 状态：浅灰边框 + 降低阴影 */
.search .el-input.search-input.is-disabled {
    border-color: var(--el-border-color-lighter, #ebeef5);
    box-shadow: none;
    opacity: 0.7;
}

/* 输入区：去默认边框/阴影，左侧圆角，加大字号 */
.search .el-input__wrapper {
    height: 56px;
    padding: 0 16px 0 24px;
    background: #fff;
    border: none;
    border-radius: 32px 0 0 32px;
    box-shadow: none !important;
}

.search .el-input__inner {
    height: 100%;
    font-size: 16px;
    color: var(--el-text-color-primary, #303133);
}

.search .el-input__inner::placeholder {
    color: #a8abb2;
}

/* 搜索按钮区（append）：主色填充，右侧圆角 */
.search .el-input-group__append {
    padding: 0 22px;
    background: var(--el-color-primary, #409eff);
    border: none;
    border-radius: 0 32px 32px 0;
}

.search .el-input-group__append .el-button {
    color: #fff;
    background: transparent;
    border: none;
    font-size: 18px;
}

.search .el-input-group__append .el-button:hover,
.search .el-input-group__append .el-button:focus {
    color: #fff;
    background: rgba(255, 255, 255, 0.15);
}
</style>