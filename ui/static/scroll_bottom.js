// Scrolls the conversation to the latest message.
(function () {
  try {
    var doc = window.parent.document;
    var container = doc.querySelector('section[data-testid="stMain"]');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  } catch (e) {}
})();