(function () {
    const bubble = document.getElementById('chatBubble');
    const chatWindow = document.getElementById('chatWindow');
    const closeBtn = document.getElementById('chatClose');
    const messagesEl = document.getElementById('chatMessages');
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('chatSend');

    function openChat() {
        chatWindow.classList.add('open');
        bubble.style.display = 'none';
        input.focus();
    }

    function closeChat() {
        chatWindow.classList.remove('open');
        bubble.style.display = 'flex';
    }

    bubble.addEventListener('click', openChat);
    closeBtn.addEventListener('click', closeChat);

    function addMessage(text, who) {
        const row = document.createElement('div');
        row.className = 'msg ' + (who === 'user' ? 'user' : 'bot');

        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.textContent = text;

        const avatar = document.createElement('span');
        avatar.className = 'avatar';
        avatar.textContent = who === 'user' ? '🙂' : '🤖';

        if (who === 'user') {
            row.appendChild(bubble);
            row.appendChild(avatar);
        } else {
            row.appendChild(avatar);
            row.appendChild(bubble);
        }

        messagesEl.appendChild(row);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        return row;
    }

    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        input.value = '';

        // Typing indicator
        const typing = document.createElement('div');
        typing.className = 'msg bot';
        typing.innerHTML = '<span class="avatar">🤖</span><div class="bubble typing">typing...</div>';
        messagesEl.appendChild(typing);
        messagesEl.scrollTop = messagesEl.scrollHeight;

        try {
            const res = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();
            typing.remove();
            addMessage(data.reply, 'bot');
        } catch (err) {
            typing.remove();
            addMessage('Sorry, something went wrong. Please try again.', 'bot');
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') sendMessage();
    });
})();
