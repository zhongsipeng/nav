import { post, request, get } from "@/utils/request";
import { appConfig } from "@/config/appConfig";

// 接口地址配置
export default function getCollect(data) {
return post(appConfig.API_URLS.GET_COLLECT, data);
}
export function saveCollect(data) {
    return post(appConfig.API_URLS.SAVE_COLLECT, data);
}
export function delCollect(data) {
    return post(appConfig.API_URLS.DEL_COLLECT, data);
}
export function batchUpdate(data) {
    return post(appConfig.API_URLS.BATCH_UPDATE, data);
}
export function importCollect(file) {
    const formData = new FormData();
    formData.append('file', file);
    return post(appConfig.API_URLS.IMPORT_COLLECT, formData, { 'Content-Type': 'multipart/form-data' }
    )
}
