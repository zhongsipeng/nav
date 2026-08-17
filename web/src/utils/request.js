import axios from 'axios';
import { appConfig } from '@/config/appConfig';
import { loadingClose, errorTip, loading } from './tip';

// 创建axios实例（可统一配置超时、baseURL等）
const service = axios.create({
  baseURL: appConfig.API_BASE_URL, // 根据环境变量设置基础URL
  timeout: appConfig.TIMEOUT, // 超时时间
});

// 请求拦截器
service.interceptors.request.use(config => {
  // 不显示loading的请求配置
  // if (!config.hideLoading) {
  loading()
  // }
  return config
})

// 响应拦截器
service.interceptors.response.use(
  response => {
    // 关闭loading
    // if (!response.config.hideLoading) {
    loadingClose()
    // }
    return response.data
  },
  error => {
    // 错误时也要关闭loading
    // if (!error.config.hideLoading) {
    loadingClose()
    // }
    return Promise.reject(error)
  }
)


/**
 * 封装请求函数
 * @param {string} url 请求地址
 * @param {object} params 请求参数（GET用params，POST用data）
 * @param {string} method 请求方法（默认GET）
 * @returns {Promise} 直接返回接口数据（response.data）
 */
export function request(url, params = {}, method = 'GET',headers) {
  const config = {
    url,
    method: method.toUpperCase(),
    headers,
    // 自动区分GET/POST参数
    ...(method.toUpperCase() === 'GET' ? { params } : { data: params })
  };

  return service(config)
    .then(response => {
      // 直接返回接口数据（根据你的后端结构调整，这里假设数据在response.data中）
      let data = response
      if (!data || typeof data !== "object" || JSON.stringify(data) === "{}") {
        throw new Error("响应数据有误！")
      }
      if (data.status !== 1) {
        throw new Error(data.message)
      }
      return data;
    })
    .catch(error => {
      // 统一错误处理（可根据项目需求定制）
      let errorMessage = '请求失败';

      if (error.response) {
        // 服务器返回了非2xx的状态码
        errorMessage = `错误码: ${error.response.status}`;
      } else if (error.request) {
        // 请求已发出但无响应
        errorMessage = '网络连接异常';
      } else {
        // 其他错误
        errorMessage = error.message;
      }

      // errorTip(errorMessage)
      // 抛出错误（可由调用方捕获处理）
      throw new Error(errorMessage);
    });
}

// 可选：导出常用方法别名
export const get = (url, params,headers) => request(url, params, 'GET',headers);
export const post = (url, params,headers) => request(url, params, 'POST',headers);