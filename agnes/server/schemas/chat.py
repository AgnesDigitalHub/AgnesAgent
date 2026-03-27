"""
聊天页面 Schema
"""


def get_chat_schema():
    """获取聊天页面 amis Schema"""
    return {
        "type": "page",
        "title": "聊天",
        "className": "chat-page",
        "body": [
            {
                "type": "custom",
                "onMount": """
(function() {
    const container = document.createElement('div');
    container.style.cssText = 'height: calc(100vh - 120px); display: flex; flex-direction: column;';
    
    // 消息区域
    const messagesDiv = document.createElement('div');
    messagesDiv.style.cssText = 'flex: 1; overflow-y: auto; padding: 20px; background: #f5f5f5;';
    messagesDiv.id = 'chat-messages';
    
    // 输入区域
    const inputDiv = document.createElement('div');
    inputDiv.style.cssText = 'padding: 20px; background: white; border-top: 1px solid #e5e5e5;';
    
    const inputWrapper = document.createElement('div');
    inputWrapper.style.cssText = 'display: flex; gap: 10px;';
    
    const input = document.createElement('textarea');
    input.placeholder = '输入消息...';
    input.style.cssText = 'flex: 1; padding: 10px; border: 1px solid #d9d9d9; border-radius: 4px; resize: none; height: 80px;';
    
    const sendBtn = document.createElement('button');
    sendBtn.textContent = '发送';
    sendBtn.style.cssText = 'padding: 10px 20px; background: #165dff; color: white; border: none; border-radius: 4px; cursor: pointer; height: 80px;';
    
    inputWrapper.appendChild(input);
    inputWrapper.appendChild(sendBtn);
    inputDiv.appendChild(inputWrapper);
    
    container.appendChild(messagesDiv);
    container.appendChild(inputDiv);
    
    // 添加到 DOM
    const root = document.getElementById('chat-container');
    if (root) {
        root.appendChild(container);
    }
    
    // 消息历史
    let messages = [];
    let isGenerating = false;
    
    function addMessage(role, content) {
        const msgDiv = document.createElement('div');
        msgDiv.style.cssText = 'margin-bottom: 20px; display: flex; ' + (role === 'user' ? 'justify-content: flex-end;' : 'justify-content: flex-start;');
        
        const bubble = document.createElement('div');
        bubble.style.cssText = 'max-width: 70%; padding: 12px 16px; border-radius: 8px; ' + 
            (role === 'user' ? 'background: #165dff; color: white;' : 'background: white; border: 1px solid #e5e5e5;');
        bubble.textContent = content;
        bubble.id = 'msg-' + Date.now();
        
        msgDiv.appendChild(bubble);
        messagesDiv.appendChild(msgDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        return bubble;
    }
    
    let currentAssistantBubble = null;
    let currentContent = '';
    
    function handleWebSocketMessage(data) {
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
            currentAssistantBubble = null;
        } else if (data.type === 'error') {
            isGenerating = false;
            addMessage('system', '错误: ' + data.message);
        }
    }
    
    // 注册消息处理器
    if (window.addChatMessageHandler) {
        window.addChatMessageHandler(handleWebSocketMessage);
    }
    
    // 发送消息
    function sendMessage() {
        const message = input.value.trim();
        if (!message || isGenerating) return;
        
        addMessage('user', message);
        input.value = '';
        
        if (window.sendChatMessage) {
            window.sendChatMessage(message, true);
        }
    }
    
    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 初始提示
    const welcomeDiv = document.createElement('div');
    welcomeDiv.style.cssText = 'text-align: center; color: #999; margin-top: 50px;';
    welcomeDiv.innerHTML = '<div style="font-size: 48px; margin-bottom: 20px;">💬</div><div>开始对话吧！</div>';
    messagesDiv.appendChild(welcomeDiv);
})();
                """,
                "html": "<div id='chat-container'></div>",
            },
        ],
    }
