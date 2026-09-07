// Adds clipboard actions to rendered chat messages.
(function () {
  function copyText(text, html) {
    var clipboard = window.parent.navigator.clipboard;
    if (clipboard && window.parent.ClipboardItem && window.parent.isSecureContext) {
      var item = new window.parent.ClipboardItem({
        'text/plain': new window.parent.Blob([text], { type: 'text/plain' }),
        'text/html': new window.parent.Blob([html || text], { type: 'text/html' })
      });
      return clipboard.write([item]);
    }
    var textarea = window.parent.document.createElement('textarea');
    textarea.value = text;
    window.parent.document.body.appendChild(textarea);
    textarea.select();
    window.parent.document.execCommand('copy');
    textarea.remove();
    return Promise.resolve();
  }

  function bind() {
    try {
      var doc = window.parent.document;
      var buttons = Array.from(doc.querySelectorAll('.chat-copy-button:not([data-bound="true"]), .chat-edit-button:not([data-bound="true"])'));
      buttons.forEach(function (button) {
        button.addEventListener('click', function () {
          if (button.classList.contains('chat-edit-button')) {
            var input = doc.querySelector('div.st-key-input_row input[type="text"]');
            if (!input) return;
            var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
            setter.call(input, button.dataset.editText || '');
            input.dispatchEvent(new window.parent.Event('input', { bubbles: true }));
            input.dispatchEvent(new window.parent.Event('change', { bubbles: true }));
            input.focus();
            return;
          }
          var text = button.dataset.copyText || '';
          var html = text;
          if (button.dataset.copyKind === 'response') {
            var content = button.closest('[data-testid="stChatMessageContent"]');
            var clone = content ? content.cloneNode(true) : null;
            if (clone) {
              clone.querySelectorAll('.chat-copy-button, .chat-action-marker').forEach(function (element) {
                element.remove();
              });
              text = clone.innerText.trim();
              html = clone.innerHTML;
            }
          }
          copyText(text, html).then(function () {
          });
        });
        button.dataset.bound = 'true';
      });
      return buttons.length > 0;
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
