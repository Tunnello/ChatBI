import api from "./index";

export const agentApi = {
  // ChatBI API
  chatQuery: (data: { query: string; session_id?: string; request_id?: string; model?: string }) => 
    api.post(`/api/chat/query`, data),
  healthCheck: () => api.get(`/api/chat/health`),
  allModels: () => api.get(`/api/chat/models`),
};
