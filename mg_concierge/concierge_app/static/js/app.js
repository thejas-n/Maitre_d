const videos = {
  idle: document.getElementById('vid-idle'),
  listening: document.getElementById('vid-listening'),
  speaking: document.getElementById('vid-speaking')
};
const statusBadge = document.getElementById('status-badge');
const interactBtn = document.getElementById('interact-btn');
const tablesGrid = document.getElementById('tables-grid');
const waitlistList = document.getElementById('waitlist-list');

const state = {
  recognition: null,
  isSpeaking: false,
  isProcessing: false,
  isListening: false,
  suppressRecognition: true,
  conversationActive: false
};

const setAvatar = (mode) => {
  Object.values(videos).forEach((video) => {
    video.classList.remove('active');
    video.pause();
  });
  const target = videos[mode];
  if (!target) return;
  target.classList.add('active');
  target.currentTime = 0;
  target.play().catch((err) => console.log('Avatar play error', err));
  statusBadge.textContent = mode.charAt(0).toUpperCase() + mode.slice(1);
};

setAvatar('idle');

const restartRecognition = (delay = 0) => {
  setTimeout(() => {
    if (
      !state.recognition ||
      state.isListening ||
      state.isSpeaking ||
      state.isProcessing ||
      state.suppressRecognition
    ) {
      return;
    }
    try {
      state.recognition.start();
    } catch (err) {
      console.warn('Recognition start failed', err);
      restartRecognition(300);
    }
  }, delay);
};

const endInteractionFlow = () => {
  state.suppressRecognition = true;
  if (state.recognition) {
    try {
      state.recognition.stop();
    } catch (err) {
      console.warn(err);
    }
  }
  state.isListening = false;
  state.isProcessing = false;
  state.conversationActive = false;
  interactBtn.style.display = 'inline-flex';
  setAvatar('idle');
};

const handleTableClick = async (tableId) => {
  if (!tableId) return;
  try {
    const res = await fetch('/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ table_id: tableId })
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      alert(data.message || 'Unable to clear this table.');
      return;
    }
    updateDashboard();
    if (data.announcement) {
      await announce(data.announcement);
    }
  } catch (err) {
    console.error('Failed to checkout table', err);
  }
};

const renderTables = (tables) => {
  tablesGrid.innerHTML = tables
    .map(
      (table) => `
      <div class="table-item ${table.status} ${table.status === 'occupied' ? 'clickable' : ''}"
           data-table-id="${table.id}">
        <strong>${table.id}</strong><br>
        ${table.seats} seats<br>
        ${table.guest_name || 'Free'}
      </div>`
    )
    .join('');

  tablesGrid.querySelectorAll('.table-item.occupied').forEach((el) => {
    el.addEventListener('click', () => handleTableClick(el.dataset.tableId));
  });
};

const renderWaitlist = (waitlist) => {
  if (!waitlist?.length) {
    waitlistList.innerHTML = '<li>Empty</li>';
    return;
  }
  waitlistList.innerHTML = waitlist
    .map((entry, index) => `<li>#${index + 1}: ${entry.name} (${entry.party_size} ppl) ${entry.eta_minutes !== null ? `(ETA: ${entry.eta_minutes} min)` : ''}</li>`)
    .join('');
};

const updateDashboard = () => {
  fetch('/api/status')
    .then((response) => response.json())
    .then((data) => {
      renderTables(data.tables);
      renderWaitlist(data.waitlist);
    })
    .catch((err) => console.error('Status refresh failed', err));
};
setInterval(updateDashboard, 2000);
updateDashboard();

const speak = async (text) => {
  if (!text) return;
  state.isSpeaking = true;
  try {
    const res = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    if (res.ok) {
      const data = await res.json();
      const audio = new Audio(`data:audio/mp3;base64,${data.audio}`);
      await new Promise((resolve) => {
        audio.onplay = () => setAvatar('speaking');
        audio.onended = resolve;
        audio.play();
      });
    } else {
      throw new Error('Server TTS failed');
    }
  } catch (err) {
    console.warn('Fallback TTS', err);
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.onstart = () => setAvatar('speaking');
    await new Promise((resolve) => {
      utterance.onend = resolve;
      window.speechSynthesis.speak(utterance);
    });
  }
  state.isSpeaking = false;
  setAvatar('idle');
};

const announce = async (text) => {
  if (!text) return;
  const wasActive = state.conversationActive;
  state.suppressRecognition = true;
  if (state.recognition && state.isListening) {
    try {
      state.recognition.stop();
    } catch (err) {
      console.warn(err);
    }
  }
  await speak(text);
  if (wasActive) {
    state.suppressRecognition = false;
    restartRecognition(250);
  } else {
    state.suppressRecognition = true;
  }
};

const handleSpeechResult = async (event) => {
  const result = event.results[event.results.length - 1][0].transcript;
  if (!result.trim()) return;
  if (state.suppressRecognition || state.isSpeaking || state.isProcessing) {
    state.recognition.stop();
    restartRecognition(350);
    return;
  }

  state.recognition.stop();
  setAvatar('idle');
  state.isProcessing = true;
  let reply = "I'm having trouble connecting.";
  let shouldEndFlow = false;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: result })
    });
    if (res.ok) {
      const data = await res.json();
      reply = data.response;
      shouldEndFlow = Boolean(data.interactionComplete);
    } else {
      console.warn('Chat request failed', res.status);
    }
  } catch (err) {
    console.error('Chat error', err);
  }

  state.isProcessing = false;
  await speak(reply);
  if (shouldEndFlow) {
    endInteractionFlow();
  } else {
    state.suppressRecognition = false;
    restartRecognition(250);
  }
};

const initSpeechRecognition = () => {
  if (!('webkitSpeechRecognition' in window)) {
    statusBadge.textContent = 'SpeechRecognition unsupported';
    return;
  }

  const recognition = new webkitSpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  recognition.onresult = handleSpeechResult;
  recognition.onerror = (event) => {
    if (event.error === 'no-speech') {
      setAvatar('idle');
      restartRecognition(400);
      return;
    }
    if (event.error === 'not-allowed') {
      statusBadge.textContent = 'Mic blocked - enable permissions';
      endInteractionFlow();
      return;
    }
    if (event.error === 'aborted') return;
    if (event.error === 'network') {
      setTimeout(() => {
        if (!state.isSpeaking && !state.isProcessing) restartRecognition(500);
      }, 1000);
    }
    console.error('Recog error', event);
  };

  recognition.onend = () => {
    state.isListening = false;
    if (!state.isSpeaking && !state.isProcessing) {
      restartRecognition(200);
    }
  };

  recognition.onstart = () => {
    state.isListening = true;
    console.log('Recognition started');
  };

  recognition.onaudiostart = () => {
    if (!state.isSpeaking) setAvatar('listening');
  };

  recognition.onsoundend = () => {
    if (!state.isSpeaking) {
      setTimeout(() => {
        if (!state.isSpeaking) setAvatar('idle');
      }, 1000);
    }
  };

  state.recognition = recognition;
};

const startInteraction = async () => {
  interactBtn.style.display = 'none';
  state.conversationActive = true;
  state.suppressRecognition = true;
  restartRecognition(0);
  await speak('Hello! Welcome to MG Cafe. How can I help you today?');
  state.suppressRecognition = false;
  restartRecognition(200);
};

interactBtn.addEventListener('click', startInteraction);
initSpeechRecognition();

