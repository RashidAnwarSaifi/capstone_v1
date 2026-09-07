// Adds Up/Down history navigation to the chat text input.
 (function () {
  function bind() {
   try {
    var doc = window.parent.document;
    var input = doc.querySelector('div.st-key-input_row input[type="text"]');
    var form = doc.querySelector('div.st-key-chat_input_bar [data-testid="stForm"]');
    if (!input || !form) return false;
    if (form.dataset.chatHistoryBound === 'true') return true;

    var markers = Array.from(doc.querySelectorAll('.chat-history-entry[data-role="user"]'));
    var history = markers.map(function (marker) { return marker.dataset.content || ''; });
    if (history.length === 0) {
      history = Array.from(doc.querySelectorAll('[data-testid="stChatMessageContent"][aria-label="Chat message from user"]'))
        .map(function (message) {
          var markdown = message.querySelector('[data-testid="stMarkdown"]');
          return markdown ? markdown.innerText.trim() : '';
        })
        .filter(Boolean);
    }
    var stored = [];
    try {
      stored = JSON.parse(window.parent.localStorage.getItem('chat-input-history') || '[]');
    } catch (error) {}
    history = history.concat(stored.filter(function (item) { return history.indexOf(item) === -1; }));
    var historyIndex = history.length;
    var changingHistory = false;

    function setValue(value) {
      changingHistory = true;
      var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
      setter.call(input, value);
      input.dispatchEvent(new window.parent.Event('input', { bubbles: true }));
      input.dispatchEvent(new window.parent.Event('change', { bubbles: true }));
      changingHistory = false;
    }

    input.addEventListener('keydown', function (event) {
      if (event.key !== 'ArrowUp' && event.key !== 'ArrowDown' || history.length === 0) return;
      event.preventDefault();
      if (event.key === 'ArrowUp') {
        historyIndex = Math.max(0, historyIndex - 1);
        setValue(history[historyIndex]);
      } else if (historyIndex < history.length - 1) {
        historyIndex += 1;
        setValue(history[historyIndex]);
      } else {
        historyIndex = history.length;
        setValue('');
      }
    });

    input.addEventListener('input', function () {
      if (!changingHistory) historyIndex = history.length;
    });

    form.addEventListener('submit', function () {
      var value = input.value.trim();
      if (!value) return;
      try {
        var saved = JSON.parse(window.parent.localStorage.getItem('chat-input-history') || '[]');
        saved = saved.filter(function (item) { return item !== value; });
        saved.push(value);
        window.parent.localStorage.setItem('chat-input-history', JSON.stringify(saved.slice(-50)));
      } catch (error) {}
    });
    form.dataset.chatHistoryBound = 'true';
    return true;
   } catch (error) {
    return false;
   }
  }

  if (!bind()) {
    var attempts = 0;
    var timer = window.setInterval(function () {
      attempts += 1;
      if (bind() || attempts >= 40) window.clearInterval(timer);
    }, 250);
  }
})();
