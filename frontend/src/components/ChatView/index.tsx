import { useEffect, useState, useRef, useMemo } from "react";
import {
  getUniqId,
  scrollToTop,
  ActionViewItemEnum,
  getSessionId,
} from "@/utils";
import querySSE from "@/utils/querySSE";
import { handleTaskData, combineData } from "@/utils/chat";
import Dialogue from "@/components/Dialogue";
import DataDialogue from "@/components/Dialogue/DataDialogue";
import GeneralInput from "@/components/GeneralInput";
import ActionView from "@/components/ActionView";
import { RESULT_TYPES } from "@/utils/constants";
import { useMemoizedFn } from "ahooks";
import classNames from "classnames";
import Logo from "../Logo";
import { Modal } from "antd";

const STORAGE_KEY_PREFIX = "chat_view_history";

const buildHistoryKey = (type: "general" | "data") =>
  `${STORAGE_KEY_PREFIX}:${type}`;

type Props = {
  inputInfo: CHAT.TInputInfo;
  product?: CHAT.Product;
};

const ChatView: GenieType.FC<Props> = (props) => {
  const { inputInfo: inputInfoProp, product } = props;

  const [chatTitle, setChatTitle] = useState("");
  const [taskList, setTaskList] = useState<MESSAGE.Task[]>([]);
  const chatList = useRef<CHAT.ChatItem[]>([]);
  const [chatListState, setChatListState] = useState<CHAT.ChatItem[]>([]); // 添加状态用于触发重新渲染
  const [dataChatList, setDataChatList] = useState<Record<string, any>[]>([]);
  const [activeTask, setActiveTask] = useState<CHAT.Task>();
  const [plan, setPlan] = useState<CHAT.Plan>();
  const [showAction, setShowAction] = useState(false);
  const [loading, setLoading] = useState(false);
  const chatRef = useRef<HTMLInputElement>(null);
  const actionViewRef = ActionView.useActionView();
  const sessionId = useMemo(() => getSessionId(), []);
  const [modal, contextHolder] = Modal.useModal();
  const generalHistoryLoadedRef = useRef(false);
  const dataHistoryLoadedRef = useRef(false);

  const combineCurrentChat = (
    inputInfo: CHAT.TInputInfo,
    sessionId: string,
    requestId: string
  ): CHAT.ChatItem => {
    return {
      query: inputInfo.message!,
      files: inputInfo.files!,
      responseType: "txt",
      sessionId,
      requestId,
      loading: true,
      forceStop: false,
      tasks: [],
      thought: "",
      response: "",
      taskStatus: 0,
      tip: "已接收到你的任务，将立即开始处理...",
      multiAgent: { tasks: [] },
    };
  };

  const sendMessage = useMemoizedFn((inputInfo: CHAT.TInputInfo) => {
    console.log("[DEBUG] ========== sendMessage called ==========");
    const { message, deepThink, outputStyle } = inputInfo;
    const requestId = getUniqId();
    let currentChat = combineCurrentChat(inputInfo, sessionId, requestId);
    chatList.current = [...chatList.current, currentChat];
    setChatListState([...chatList.current]); // 触发重新渲染
    if (!chatTitle) {
      setChatTitle(message!);
    }
    setLoading(true);
    const params = {
      query: message,
      session_id: sessionId,
      request_id: requestId,
      model: "qwen-plus", // 可以根据需要选择模型
    };
    const handleMessage = (data: any) => {
      try {
        // 适配我们的后端响应格式
        console.log("[DEBUG] ========== handleMessage called in sendMessage ==========");
        console.log("[DEBUG] Received SSE message in sendMessage:", data);
        console.log("[DEBUG] Current chatList length:", chatList.current.length);
        console.log("[DEBUG] currentChat object:", currentChat);
        
        if (!data) {
          console.error("[ERROR] handleMessage received null or undefined data");
          return;
        }
        
        const { type, message: responseMessage, finished } = data; // 重命名避免冲突
        console.log("[DEBUG] Parsed values:", { type, responseMessage, finished });
        
        if (type === "error") {
        console.log("[DEBUG] Error message received:", responseMessage);
        currentChat.loading = false;
        currentChat.response = responseMessage || "处理请求时出错";
        setLoading(false);
        const newChatList = [...chatList.current];
        newChatList.splice(newChatList.length - 1, 1, currentChat);
        chatList.current = newChatList;
        setChatListState([...newChatList]); // 触发重新渲染
        scrollToTop(chatRef.current!);
        return;
      }
      
      if (type === "start") {
        // 初始消息，更新 tip
        console.log("[DEBUG] Start message:", responseMessage);
        currentChat.tip = responseMessage || "已接收到你的任务，将立即开始处理...";
        currentChat.loading = true;
        const newChatList = [...chatList.current];
        newChatList.splice(newChatList.length - 1, 1, currentChat);
        chatList.current = newChatList;
        setChatListState([...newChatList]); // 触发重新渲染
        scrollToTop(chatRef.current!);
      } else if (type === "response") {
        console.log("[DEBUG] Response message:", { responseMessage, finished, messageLength: responseMessage?.length });
        // 收到响应时，清除 tip，显示 response
        if (responseMessage !== undefined) {
          currentChat.response = responseMessage || "";
          currentChat.tip = ""; // 清除 tip，只显示 response
          currentChat.loading = !finished;
          if (finished) {
            console.log("[DEBUG] Message finished, stopping loading");
            setLoading(false);
          }
          const newChatList = [...chatList.current];
          newChatList.splice(newChatList.length - 1, 1, currentChat);
          chatList.current = newChatList;
          setChatListState([...newChatList]); // 触发重新渲染
          console.log("[DEBUG] Updated chat list, response:", currentChat.response);
          console.log("[DEBUG] Chat object:", JSON.stringify(currentChat, null, 2));
        }
        scrollToTop(chatRef.current!);
      } else {
        console.log("[DEBUG] Unknown message type:", type);
      }
      } catch (error) {
        console.error("[ERROR] Error in handleMessage:", error);
        console.error("[ERROR] Error stack:", (error as Error).stack);
        console.error("[ERROR] Data that caused error:", data);
      }
    };

    const openAction = (taskList: MESSAGE.Task[]) => {
      if (
        taskList.filter((t) => !RESULT_TYPES.includes(t.messageType)).length
      ) {
        setShowAction(true);
      }
    };

    const handleError = (error: unknown) => {
      throw error;
    };

    const handleClose = () => {
      console.log("🚀 ~ close");
    };

    querySSE(
      {
        body: params,
        handleMessage,
        handleError,
        handleClose,
      },
      `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/chat/query`
    );
  });

  useEffect(() => {
    if (typeof window === "undefined" || !sessionId) {
      return;
    }
    const historyKey = buildHistoryKey("general");
    try {
      const raw = window.localStorage.getItem(historyKey);
      if (raw) {
        const legacy = JSON.parse(raw);
        if (legacy?.chatList && Array.isArray(legacy.chatList)) {
          chatList.current = legacy.chatList;
          setChatListState(legacy.chatList);
        }
        if (legacy?.chatTitle) {
          setChatTitle(legacy.chatTitle);
        }
        if (legacy?.sessionId) {
          // 如果存在历史的 sessionId，则复用它，便于继续对话
          chatList.current = legacy.chatList || [];
        }
      }
    } catch (error) {
      console.error("[ERROR] Failed to load general chat history:", error);
    } finally {
      generalHistoryLoadedRef.current = true;
    }
  }, [sessionId]);

  useEffect(() => {
    if (typeof window === "undefined" || !sessionId) {
      return;
    }
    const historyKey = buildHistoryKey("data");
    try {
      const raw = window.localStorage.getItem(historyKey);
      if (raw) {
        const legacy = JSON.parse(raw);
        if (legacy?.dataChatList && Array.isArray(legacy.dataChatList)) {
          setDataChatList(legacy.dataChatList);
        }
        if (legacy?.chatTitle) {
          setChatTitle(legacy.chatTitle);
        }
      }
    } catch (error) {
      console.error("[ERROR] Failed to load data chat history:", error);
    } finally {
      dataHistoryLoadedRef.current = true;
    }
  }, [sessionId]);

  useEffect(() => {
    if (!generalHistoryLoadedRef.current || typeof window === "undefined" || !sessionId) {
      return;
    }
    const historyKey = buildHistoryKey("general");
    if (chatListState.length === 0) {
      window.localStorage.removeItem(historyKey);
      return;
    }
    try {
      window.localStorage.setItem(
        historyKey,
        JSON.stringify({
          chatList: chatListState,
          chatTitle,
          sessionId,
        })
      );
    } catch (error) {
      console.error("[ERROR] Failed to persist general chat history:", error);
    }
  }, [chatListState, chatTitle, sessionId]);

  useEffect(() => {
    if (!dataHistoryLoadedRef.current || typeof window === "undefined" || !sessionId) {
      return;
    }
    const historyKey = buildHistoryKey("data");
    if (dataChatList.length === 0) {
      window.localStorage.removeItem(historyKey);
      return;
    }
    try {
      window.localStorage.setItem(
        historyKey,
        JSON.stringify({
          dataChatList,
          chatTitle,
          sessionId,
        })
      );
    } catch (error) {
      console.error("[ERROR] Failed to persist data chat history:", error);
    }
  }, [dataChatList, chatTitle, sessionId]);

  const temporaryChangeTask = (taskList: MESSAGE.Task[]) => {
    const task = taskList[taskList.length - 1] as CHAT.Task;
    if (!["task_summary", "result"].includes(task?.messageType)) {
      setActiveTask(task);
    }
  };

  const changeTask = (task: CHAT.Task) => {
    actionViewRef.current?.changeActionView(ActionViewItemEnum.follow);
    changeActionStatus(true);
    setActiveTask(task);
  };

  const updatePlan = (plan: CHAT.Plan) => {
    setPlan(plan);
  };

  const changeFile = (file: CHAT.TFile) => {
    changeActionStatus(true);
    actionViewRef.current?.setFilePreview(file);
  };

  const changePlan = () => {
    changeActionStatus(true);
    actionViewRef.current?.openPlanView();
  };

  const changeActionStatus = (status: boolean) => {
    setShowAction(status);
  };

  const sendDataMessage = (inputInfo: any) => {
    console.log("[DEBUG] ========== sendDataMessage called ==========");
    const requestId = getUniqId();
    const params = {
      query: inputInfo.message,
      session_id: sessionId,
      request_id: requestId,
      model: "qwen-plus",
    };
    let currentChat = {
      query: inputInfo.message,
      loading: true,
      think: "",
      chartData: undefined,
      error: "",
      response: "",
      requestId,
    };
    setDataChatList((prev) => [...prev, { ...currentChat }]);
    scrollToTop(chatRef.current!);

    setChatTitle(inputInfo.message);
    setLoading(true);

    const mergeChatUpdate = (patch: Partial<typeof currentChat>) => {
      currentChat = { ...currentChat, ...patch };
      setDataChatList((prev) =>
        prev.map((chat) =>
          chat.requestId === requestId ? { ...chat, ...currentChat } : chat
        )
      );
    };

    const handleMessage = (data: any) => {
      try {
        console.log("[DEBUG] ========== handleMessage called in sendDataMessage ==========");
        console.log("[DEBUG] Received SSE message in sendDataMessage:", data);
        // 适配我们的后端响应格式
        const { type, message, finished } = data;
        console.log("[DEBUG] Parsed values in sendDataMessage:", { type, message, finished });
        
        if (type === "error") {
          console.log("[DEBUG] Error message in sendDataMessage:", message);
          mergeChatUpdate({
            error: message || "处理请求时出错",
            loading: false,
          });
          setLoading(false);
        } else if (type === "start") {
          console.log("[DEBUG] Start message in sendDataMessage:", message);
          mergeChatUpdate({
            think: message || "正在处理...",
            loading: true,
            error: "",
          });
        } else if (type === "response") {
          console.log("[DEBUG] Response message in sendDataMessage:", { message, finished });
          // 尝试解析消息中的图表数据
          try {
            // 提取 JSON 的辅助方法（尽量健壮）
            const extractChartJsonFromText = (text: string): any | null => {
              if (!text) return null;
              const candidates: string[] = [];
              // 1) 捕获所有代码块 ```...```
              const fenceRegex = /```(?:json|JSON)?\s*([\s\S]*?)\s*```/g;
              let fenceMatch;
              while ((fenceMatch = fenceRegex.exec(text)) !== null) {
                if (fenceMatch[1]) candidates.push(fenceMatch[1]);
              }
              // 2) 捕获疑似 JSON 对象（通过简单的括号平衡提取多段）
              //    仅当未在代码块中捕获到时再做
              if (candidates.length === 0) {
                const chars = Array.from(text);
                let depth = 0;
                let start = -1;
                for (let i = 0; i < chars.length; i++) {
                  if (chars[i] === "{") {
                    if (depth === 0) start = i;
                    depth++;
                  } else if (chars[i] === "}") {
                    if (depth > 0) depth--;
                    if (depth === 0 && start !== -1) {
                      const snippet = text.substring(start, i + 1);
                      // 过滤太短的片段
                      if (snippet.length > 2) candidates.push(snippet);
                      start = -1;
                    }
                  }
                }
              }
              // 3) 遍历候选，选择包含关键字段的对象
              const importantKeys = ["series", "dimCols", "measureCols", "dataList", "option", "chartSuggest", "xAxis"];
              for (const c of candidates) {
                try {
                  const obj = JSON.parse(c);
                  const keys = Object.keys(obj || {});
                  const hit = importantKeys.some((k) => k in obj);
                  if (hit) return obj;
                  // 兜底：如果有 chart_config 嵌套
                  if (obj && typeof obj === "object" && obj.chart_config) {
                    return obj.chart_config;
                  }
                } catch {
                  // 忽略解析失败
                }
              }
              return null;
            };
            const parsed = extractChartJsonFromText(message);
            if (parsed) {
              mergeChatUpdate({
                chartData: parsed,
              });
            }
            mergeChatUpdate({
              response: message,
            });
          } catch (e) {
            mergeChatUpdate({
              response: message,
            });
          }
          if (finished) {
            console.log("[DEBUG] Message finished in sendDataMessage");
            mergeChatUpdate({
              loading: false,
            });
            setLoading(false);
          }
        }
        console.log("[DEBUG] Updated dataChatList, response:", currentChat.response);
        // 滚动到顶部
        scrollToTop(chatRef.current!);
      } catch (error) {
        console.error("[ERROR] Error in sendDataMessage handleMessage:", error);
        console.error("[ERROR] Error stack:", (error as Error).stack);
        console.error("[ERROR] Data that caused error:", data);
      }
    };
    const handleError = (error: unknown) => {
      throw error;
    };

    const handleClose = () => {
      console.log("🚀 ~ close");
    };
    querySSE(
      {
        body: params,
        handleMessage,
        handleError,
        handleClose,
      },
      `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/chat/query`
    );
  };

  useEffect(() => {
    if (inputInfoProp.message?.length !== 0) {
      product?.type === "dataAgent" && !inputInfoProp.deepThink
        ? sendDataMessage(inputInfoProp)
        : sendMessage(inputInfoProp);
    }
  }, [inputInfoProp, sendMessage]);

  const renderMultAgent = () => {
    return (
      <div className="h-full w-full flex justify-center">
        <div
          className={classNames("p-24 flex flex-col flex-1 w-0", {
            "max-w-[1200px]": !showAction,
          })}
          id="chat-view"
        >
          <div className="w-full flex justify-between">
            <div className="w-full flex items-center pb-8">
              <Logo />
              <div className="overflow-hidden whitespace-nowrap text-ellipsis text-[16px] font-[500] text-[#27272A] mr-8">
                {chatTitle}
              </div>
              {inputInfoProp.deepThink && (
                <div className="rounded-[4px] px-6 border-1 border-solid border-gray-300 flex items-center shrink-0">
                  <i className="font_family icon-shendusikao mr-6 text-[12px]"></i>
                  <span className="ml-[-4px]">深度研究</span>
                </div>
              )}
            </div>
          </div>
          <div
            className="w-full flex-1 overflow-auto no-scrollbar mb-[36px]"
            ref={chatRef}
          >
            {chatListState.map((chat) => {
              return (
                <div key={chat.requestId}>
                  <Dialogue
                    chat={chat}
                    deepThink={inputInfoProp.deepThink}
                    changeTask={changeTask}
                    changeFile={changeFile}
                    changePlan={changePlan}
                  />
                </div>
              );
            })}
          </div>
          <GeneralInput
            placeholder={
              loading ? "任务进行中" : "希望 Genie 为你做哪些任务呢？"
            }
            showBtn={false}
            size="medium"
            disabled={loading}
            product={product}
            // 多轮问答也不支持切换deepThink，使用传进来的
            send={(info) =>
              sendMessage({
                ...info,
                deepThink: inputInfoProp.deepThink,
              })
            }
          />
        </div>
        {contextHolder}
        <div
          className={classNames("transition-all w-0", {
            "opacity-0 overflow-hidden": !showAction,
            "flex-1": showAction,
          })}
        >
          <ActionView
            activeTask={activeTask}
            taskList={taskList}
            plan={plan}
            ref={actionViewRef}
            onClose={() => changeActionStatus(false)}
          />
        </div>
      </div>
    );
  };

  const renderDataAgent = () => {
    return (
      <div
        className={classNames("p-24 flex flex-col flex-1 w-0 max-w-[1200px]")}
      >
        <div className="w-full flex justify-between">
          <div className="w-full flex items-center pb-8">
            <Logo />
            <div className="overflow-hidden whitespace-nowrap text-ellipsis text-[16px] font-[500] text-[#27272A] mr-8">
              {chatTitle}
            </div>
          </div>
        </div>
        <div
          className="w-full flex-1 overflow-auto no-scrollbar mb-[36px]"
          ref={chatRef}
        >
          {dataChatList.map((chat, index) => {
            return (
              <div key={index}>
                <DataDialogue chat={chat} />
              </div>
            );
          })}
        </div>
        <GeneralInput
          placeholder={loading ? "任务进行中" : "希望 Genie 为你做哪些任务呢？"}
          showBtn={false}
          size="medium"
          disabled={loading}
          product={product}
          send={(info) =>
            sendDataMessage({
              ...info,
            })
          }
        />
      </div>
    );
  };

  return (
    <div className="h-full w-full flex justify-center">
      {product?.type === "dataAgent" && !inputInfoProp.deepThink
        ? renderDataAgent()
        : renderMultAgent()}
    </div>
  );
};

export default ChatView;
