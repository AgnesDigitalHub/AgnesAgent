"""
聊天页面 Schema - 使用 python-amis 构建
"""

from amis.amis import amis


def get_chat_schema():
    """获取聊天页面 amis Schema"""
    a = amis()
    
    custom = a.Custom()
    custom.onMount("""
(function() {
    // 构建完整界面
    const container = document.createElement('div');
    container.style.cssText = 'height: calc(100vh - 120px); display: flex; flex-direction: column; background: #f5f5f5;';
    
    // 状态栏：显示当前模型和清空按钮
    const statusBar = document.createElement('div');
    statusBar.style.cssText = 'padding: 10px 20px; background: white; border-bottom: 1px solid #e5e5e5; display: flex; justify-content: space-between; align-items: center;';
    
    const statusText = document.createElement('div');
    statusText.id = 'status-text';
    statusText.style.cssText = 'font-size: 14px; color: #666;';
    statusText.textContent = '检查模型状态...';
    
    const clearBtn = document.createElement('button');
    clearBtn.textContent = '清空对话';
    clearBtn.style.cssText = 'padding: 6px 16px; background: #f5f5f5; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer;';
    clearBtn.onclick = function() {
        if (messagesDiv) {
            messagesDiv.innerHTML = '';
            chatHistory = [];
            const welcomeDiv = document.createElement('div');
            welcomeDiv.style.cssText = 'text-align: center; color: #999; margin-top: 50px;';
            welcomeDiv.innerHTML = '<div style="font-size: 48px; margin-bottom: 20px;">💬</div><div>开始对话吧！</div>';
            messagesDiv.appendChild(welcomeDiv);
        }
    };
    
    statusBar.appendChild(statusText);
    statusBar.appendChild(clearBtn);
    
    // 消息区域
    const messagesDiv = document.createElement('div');
    messagesDiv.style.cssText = 'flex: 1; overflow-y: auto; padding: 20px;';
    
    // 输入区域
    const inputDiv = document.createElement('div');
    inputDiv.style.cssText = 'padding: 20px; background: white; border-top: 1px solid #e5e5e5;';
    
    const inputWrapper = document.createElement('div');
    inputWrapper.style.cssText = 'display: flex; gap: 10px;';
    
    const input = document.createElement('textarea');
    input.placeholder = '输入消息，按 Enter 发送，Shift + Enter 换行...';
    input.style.cssText = 'flex: 1; padding: 10px; border: 1px solid #d9d9d9; border-radius: 4px; resize: none; height: 80px; font-size: 14px;';
    
    const sendBtn = document.createElement('button');
    sendBtn.textContent = '发送';
    sendBtn.style.cssText = 'padding: 10px 28px; background: #165dff; color: white; border: none; border-radius: 4px; cursor: pointer; height: 80px; font-size: 14px;';
    
    inputWrapper.appendChild(input);
    inputWrapper.appendChild(sendBtn);
    inputDiv.appendChild(inputWrapper);
    
    container.appendChild(statusBar);
    container.appendChild(messagesDiv);
    container.appendChild(inputDiv);
    
    // 添加到 DOM
    const root = document.getElementById('chat-container');
    if (root) {
        root.appendChild(container);
    }
    
    // ============ WebSocket 连接逻辑 ============
    let ws = null;
    let isGenerating = false;
    let chatHistory = [];
    let currentAssistantBubble = null;
    let currentContent = '';
    
    // 获取协议：HTTP -> ws, HTTPS -> wss
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = protocol + '//' + window.location.host + '/ws/chat';
    
    function connect() {
        console.log('连接 WebSocket:', wsUrl);
        ws = new WebSocket(wsUrl);
        
        ws.onopen = function() {
            console.log('WebSocket 连接成功');
            checkStatus();
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleMessage(data);
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket 错误:', error);
            statusText.textContent = '⚠️ 连接错误';
            addSystemMessage('WebSocket 连接失败，请检查后端服务');
        };
        
        ws.onclose = function() {
            console.log('WebSocket 连接关闭');
            statusText.textContent = '🔌 连接断开';
        };
    }
    
    function handleMessage(data) {
        if (data.type === 'start') {
            isGenerating = true;
            currentContent = '';
            currentAssistantBubble = addMessage('assistant', '');
        } else if (data.type === 'token') {
            currentContent += data.content;
            if (currentAssistantBubble) {
                currentAssistantBubble.textContent = currentContent;
            }
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        } else if (data.type === 'done') {
            isGenerating = false;
            if (currentAssistantBubble) {
                chatHistory.push({role: 'assistant', content: currentContent});
            }
            currentAssistantBubble = null;
        } else if (data.type === 'error') {
            isGenerating = false;
            addSystemMessage('错误: ' + data.message);
        }
    }
    
    function addMessage(role, content) {
        const msgDiv = document.createElement('div');
        msgDiv.style.cssText = 'margin-bottom: 20px; display: flex; ' + 
            (role === 'user' ? 'justify-content: flex-end;' : 'justify-content: flex-start;');
        
        const bubble = document.createElement('div');
        let style = 'max-width: 70%; padding: 12px 16px; border-radius: 12px; ';
        if (role === 'user') {
            style += 'background: #165dff; color: white;';
        } else if (role === 'system') {
            style += 'background: #fffbe6; border: 1px solid #ffe58f; color: #faad14;';
        } else {
            style += 'background: white; border: 1px solid #e5e5e5; color: #333;';
        }
        bubble.style.cssText = style;
        bubble.textContent = content;
        
        msgDiv.appendChild(bubble);
        messagesDiv.appendChild(msgDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        return bubble;
    }
    
    function addSystemMessage(content) {
        const div = document.createElement('div');
        div.style.cssText = 'text-align: center; margin: 10px 0;';
        div.innerHTML = '<span style="background: #f0f0f0; padding: 4px 12px; border-radius: 12px; font-size: 12px; color: #999;">' + content + '</span>';
        messagesDiv.appendChild(div);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
    
    function sendMessage() {
        const message = input.value.trim();
        if (!message || isGenerating || !ws || ws.readyState !== WebSocket.OPEN) {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                addSystemMessage('WebSocket 未连接，请刷新页面重试');
            }
            return;
        }
        
        // 添加用户消息
        addMessage('user', message);
        chatHistory.push({role: 'user', content: message});
        input.value = '';
        
        // 发送到服务器
        ws.send(JSON.stringify({
            message: message,
            use_history: true
        }));
    }
    
    // 检查当前状态
    async function checkStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            
            if (data.has_active) {
                statusText.textContent = `✅ 当前模型: ${data.active_profile_name} (${data.llm_provider})`;
            } else {
                statusText.textContent = '⚠️ 未激活任何模型，请先去模型管理激活';
                addSystemMessage('请先在「模型管理」中添加并激活一个 LLM 配置');
            }
        } catch (e) {
            statusText.textContent = '⚠️ 无法获取状态';
            console.error('获取状态失败:', e);
        }
    }
    
    // 事件绑定
    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 初始欢迎
    const welcomeDiv = document.createElement('div');
    welcomeDiv.style.cssText = 'text-align: center; color: #999; margin-top: 50px;';
    welcomeDiv.innerHTML = '<div style="font-size: 48px; margin-bottom: 20px;">💬</div><div>开始对话吧！</div>';
    messagesDiv.appendChild(welcomeDiv);
    
    // 连接 WebSocket
    connect();
    checkStatus();
})();
    """)
    custom.html("<div id='chat-container' style='width: 100%; height: 100%;'></div>")

    page = a.Page()
    page.title("聊天")
    page.className("chat-page")
    page.body([custom])

    return page.to_dict()
