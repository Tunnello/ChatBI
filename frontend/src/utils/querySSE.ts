import { fetchEventSource, EventSourceMessage } from '@microsoft/fetch-event-source';

// 后端 API 基础 URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const DEFAULT_SSE_URL = `${API_BASE_URL}/api/chat/query`;

const SSE_HEADERS = {
  'Content-Type': 'application/json',
  'Cache-Control': 'no-cache',
  'Connection': 'keep-alive',
  'Accept': 'text/event-stream',
};

interface SSEConfig {
  body: any;
  handleMessage: (data: any) => void;
  handleError: (error: Error) => void;
  handleClose: () => void;
}

/**
 * 创建服务器发送事件（SSE）连接
 * @param config SSE 配置
 * @param url 可选的自定义 URL
 */
export default (config: SSEConfig, url: string = DEFAULT_SSE_URL): void => {
  const { body = null, handleMessage, handleError, handleClose } = config;

  console.log("[DEBUG] querySSE called with config:");
  console.log("[DEBUG] handleMessage in querySSE:", handleMessage);
  console.log("[DEBUG] handleMessage type in querySSE:", typeof handleMessage);
  console.log("[DEBUG] handleMessage.toString() in querySSE:", handleMessage?.toString().substring(0, 200));

  fetchEventSource(url, {
    method: 'POST',
    credentials: 'omit',
    headers: SSE_HEADERS,
    body: JSON.stringify(body),
    openWhenHidden: true,
    onmessage(event: EventSourceMessage) {
      console.log("[DEBUG] Raw SSE event:", event);
      if (event.data) {
        try {
          const parsedData = JSON.parse(event.data);
          console.log("[DEBUG] Parsed SSE data:", parsedData);
          console.log("[DEBUG] Calling handleMessage callback, type:", typeof handleMessage);
          if (typeof handleMessage === 'function') {
            try {
          handleMessage(parsedData);
              console.log("[DEBUG] handleMessage called successfully");
            } catch (error) {
              console.error('[ERROR] Error in handleMessage:', error);
              handleError(error as Error);
            }
          } else {
            console.error('[ERROR] handleMessage is not a function:', handleMessage);
          }
        } catch (error) {
          console.error('[ERROR] Error parsing SSE message:', error, 'Raw data:', event.data);
          handleError(new Error('Failed to parse SSE message'));
        }
      } else {
        console.log("[DEBUG] SSE event with no data:", event);
      }
    },
    onerror(error: Error) {
      console.error('SSE error:', error);
      handleError(error);
    },
    onclose() {
      console.log('SSE connection closed');
      handleClose();
    }
  });
};
