/**
 * Axios request wrapper with unified code/message interception.
 *
 * All backend responses follow: { code: 0, message: "ok", data: ... }
 * Non-zero code triggers an Element Plus error notification.
 */

import axios from "axios";
import { ElMessage } from "element-plus";

const http = axios.create({
  baseURL: "/api",
  timeout: 15000,
});

// Response interceptor: unwrap backend envelope
http.interceptors.response.use(
  (res) => {
    const body = res.data;
    if (body && body.code !== undefined && body.code !== 0) {
      ElMessage.error(body.message || "请求失败");
      return Promise.reject(new Error(body.message));
    }
    return body?.data !== undefined ? body.data : body;
  },
  (err) => {
    ElMessage.error(err.message || "网络错误");
    return Promise.reject(err);
  }
);

export default http;
