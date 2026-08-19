<template>
    <div>

        <div v-show="!collapse">

            <el-input v-model="filterText" placeholder="" clearable />
            <el-tree ref="treeRef" style="max-width: 600px" :allow-drop="allowDrop" :allow-drag="allowDrag" :data="data"
                draggable node-key="id" highlight-current :current-node-key="currentNodeKey"
                @node-drag-start="handleDragStart" @node-drag-enter="handleDragEnter" @node-drag-leave="handleDragLeave"
                @node-drag-over="handleDragOver" @node-drag-end="handleDragEnd" @node-drop="handleDrop"
                :filter-node-method="filterNode" :expand-on-click-node="false" @current-change="handleCurrentChange">
                <template #default="{ node, data }">
                    <div class="custom-tree-node">
                        <el-popover placement="bottom-start" trigger="contextmenu" :width="10">
                            <el-space direction="vertical">
                                <el-button link @click="add(data)">
                                    <el-icon>
                                        <CirclePlus />
                                    </el-icon>
                                    新增
                                </el-button>
                                <el-button link @click="edit(data)">
                                    <el-icon>
                                        <Edit />
                                    </el-icon>修改</el-button>
                                <el-button link @click="$emit('update', 'del', data)">
                                    <el-icon>
                                        <Delete />
                                    </el-icon>
                                    删除</el-button>
                            </el-space>

                            <template #reference>
                                <div @click="$emit('click', data)" style="width: 100%;">
                                    <el-icon class="section-icon" v-if="data.type == 'folder'">
                                        <Folder />
                                    </el-icon>
                                    <img v-else :src="data.icon || appConfig.LOGO_URL"
                                        style="width: 16px;height: 16px; margin-right: 5px;" />
                                    <span>{{ node.label }}</span>
                                    <!-- <el-button type="primary" link @click="append(data)">
                                        <el-icon>
                                            <CirclePlus />
                                        </el-icon>
                                    </el-button>
                                    <el-button style="margin-left: 4px" type="danger" link @click="remove(node, data)">
                                        <el-icon>
                                            <Delete />
                                        </el-icon>
                                    </el-button> -->
                                </div>
                            </template>

                        </el-popover>

                    </div>
                </template>
            </el-tree>
        </div>
    </div>
    <el-dialog v-model="dialogFormVisible" title="表单" width="500" :lock-scroll="false">
        <el-form :model="form">
            <el-radio-group v-model="form.type">
                <el-radio value="bookmark" size="large">网站</el-radio>
                <el-radio value="folder" size="large">文件夹</el-radio>
            </el-radio-group>
            <el-form-item label="名称" :label-width="formLabelWidth" >
                <el-input v-model="form.name" autocomplete="off"
                    :placeholder="pupopObj.namePlaceholder" />
            </el-form-item>
            <el-form-item v-if="form.type == 'bookmark'" label="URL" :label-width="formLabelWidth" :required="form.type === 'bookmark'">
                <el-input v-model="form.url" autocomplete="off" placeholder="请输入网址" />
            </el-form-item>
        </el-form>
        <template #footer>
            <div class="dialog-footer">
                <el-button @click="dialogFormVisible = false">取消</el-button>
                <el-button type="primary" @click="handleConfirm">
                    确认
                </el-button>
            </div>
        </template>
    </el-dialog>
</template>

<script lang="ts" setup>
import { TreeInstance } from 'element-plus'
import type Node from 'element-plus/es/components/tree/src/model/node'
import type { DragEvents } from 'element-plus/es/components/tree/src/model/useDragNode'
import { Folder, CirclePlus, Delete, Edit } from '@element-plus/icons-vue'

import type {
    AllowDropType,
    NodeDropType,
} from 'element-plus/es/components/tree/src/tree.type'
import { nextTick, PropType, reactive, ref, watch } from 'vue'
import { customConfirm, successTip } from '@/utils/tip'
import getCollect, { batchUpdate, saveCollect } from '@/api/collect'
import { appConfig } from '@/config/appConfig'
const props = defineProps({
    data: {
        type: Array as PropType<Tree[]>,
        default: () => []
    },
    collapse: {
        type: Boolean,
        default: false
    }
})

const emit = defineEmits(['click', 'update', "dropupdate"])

interface Tree {
    [key: string]: any
}
const filterText = ref('')
const treeRef = ref<TreeInstance>()
const currentNodeKey = ref<any>(null)

// 当前节点变化时通知父组件
const handleCurrentChange = (data: Tree | null, node: Node | null) => {
    if (data) {
        emit('click', data)
    }
}

// 数据变化后自动选中第一个节点并展开
watch(() => props.data, (newData) => {
    if (newData && newData.length > 0) {
        nextTick(() => {
            const first = newData[0]
            currentNodeKey.value = first.id
            // 展开第一个节点
            if (treeRef.value) {
                treeRef.value.setCurrentKey(first.id)
                try {
                    // 展开第一个节点的子节点
                    const store = (treeRef.value as any).store
                    if (store && store.nodesMap && store.nodesMap[first.id]) {
                        store.nodesMap[first.id].expanded = true
                    }
                } catch (e) { /* ignore */ }
            }
        })
    }
}, { immediate: true, deep: false })
const handleDragStart = (node: Node, ev: DragEvents) => {
    // console.log('drag start', node)
}
const filterNode = (value: string, data: Tree) => {
    if (!value) return true
    return data.label.includes(value)
}
watch(filterText, (val) => {
    treeRef.value!.filter(val)
})
const handleDragEnter = (
    draggingNode: Node,
    dropNode: Node,
    ev: DragEvents
) => {
    console.log('tree drag enter:', dropNode)
}
const handleDragLeave = (
    draggingNode: Node,
    dropNode: Node,
    ev: DragEvents
) => {
    // console.log('tree drag leave:', dropNode.label)
}
const handleDragOver = (draggingNode: Node, dropNode: Node, ev: DragEvents) => {
    // console.log('tree drag over:', dropNode.label)

}
const handleDragEnd = (
    draggingNode: Node,
    dropNode: Node,
    dropType: NodeDropType,
    ev: DragEvents
) => {
    // console.log('tree drag end:', dropNode && dropNode.label, dropType)
}
const handleDrop = (
    draggingNode,
    dropNode,
    dropType: NodeDropType,
    ev: DragEvents
) => {
    switch (dropType) {
        case "inner":
            let data = {
                "id": draggingNode.data.id,
                "pid": draggingNode.data.pid,
                // "depth": draggingNode.data.depth,
                "px": draggingNode.data.px,
            }
            data.pid = dropNode.data.id
            data.px = 0
            if (dropNode.data.children.length > 1) {
                // console.log(dropNode.data.children[dropNode.data.children.length - 1])
                data.px = dropNode.data.children[dropNode.data.children.length - 2].px + 1
            }
            // emit('update', "edit", data)
            batchUpdate({ data: [data] }).then((res) => {
                // successTip("更新成功！")
                emit('dropupdate', dropNode.parent.data)
            })
            // data.depth = dropNode.data.depth + 1
            break;
        case "before": case "after":
            let arr
            if (Array.isArray(dropNode.parent.data)) {
                arr = dropNode.parent.data.map((x, i) => {
                    return {
                        id: x.id,
                        px: i + 1,
                        pid: dropNode.data.pid
                    }
                })
            } else {

                arr = dropNode.parent.data.children.map((x, i) => {
                    return {
                        id: x.id,
                        px: i + 1,
                        pid: dropNode.data.pid
                    }
                })
            }

            batchUpdate({ data: arr }).then((res) => {
                emit('dropupdate', dropNode.parent.data)

            })
            // data.depth = dropNode.data.depth
            break;

    }
    // console.log('tree drop:', draggingNode.label, dropNode.label, dropType)
}
const allowDrop = (draggingNode: Node, dropNode: Node, type: AllowDropType) => {
    if (dropNode.data.type == "folder") {
        return true
    } else {
        return type !== 'inner'
    }

}

const formLabelWidth = '140px'
const pupopObj = reactive({
    namePlaceholder: "",
    urlRequired: true
})
const dialogFormVisible = ref(false)
const form = reactive({
    name: "",
    url: "",
    type: "bookmark",
    id: null,
    pid: null,
    // depth: null,
})

watch(
    () => form.type,              // 监听具体属性
    (newType, oldType) => {
        // 根据新值修改变量
        if (newType === 'bookmark') {
            pupopObj.urlRequired = true
            pupopObj.namePlaceholder = "不填则自动获取网站标题";

            // 可能还需要强制 url 不能为空等逻辑
        } else if (newType === 'folder') {
            pupopObj.urlRequired = false
            pupopObj.namePlaceholder = "请输入名称"
            // 比如清空 url（如果允许）
            // form.url = ''
        }
    },
    { immediate: true }           // 可选：立即执行一次，用于初始化
)
const allowDrag = (draggingNode: Node) => {
    return !draggingNode.data.label.includes('Level three 3-1-1')
}
// const append = (item: Tree) => {
//     const newChild = { id: id++, label: 'testtest', children: [] }
//     if (!item.children) {
//         item.children = []
//     }
//     item.children.push(newChild)
//     data.value = [...data.value]

// }

// const remove = (node: Node, item: Tree) => {
//     const parent = node.parent
//     const children: Tree[] = parent.data.children || parent.data
//     const index = children.findIndex((d) => d.id === item.id)
//     children.splice(index, 1)
//     data.value = [...data.value]
// }
// // const data = ref<Tree[]>(tree_data)

const add = (item) => {
    form.name = ""
    form.url = ""
    form.type = "bookmark"
    form.id = null
    form.pid = item.type == "bookmark" ? item.pid : item.id
    // form.depth = item.depth
    dialogFormVisible.value = true;
}
const edit = (item) => {
    form.name = item.label
    form.url = item.url
    form.type = item.type
    form.id = item.id
    form.pid = item.pid
    // form.depth = item.depth
    dialogFormVisible.value = true;

}

const handleConfirm = () => {
    emit('update', 'edit', form)
    dialogFormVisible.value = false
}
</script>
<style>
.custom-tree-node {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 14px;
    padding-right: 8px;
}

.section-icon {
    font-size: 18px;
    color: var(--el-color-primary);
    margin-right: 8px;
}
</style>