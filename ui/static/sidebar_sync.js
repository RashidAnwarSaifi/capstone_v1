// Publishes the sidebar's real on-screen width as the --sidebar-w CSS
// variable, so the fixed chat input bar and user badge (styles.css) can size
// themselves against it and follow the sidebar as it's resized or collapsed.
(function () {
  function sync() {
    try {
      var doc = window.parent.document;
      var sidebar = doc.querySelector('[data-testid="stSidebar"]');
      var width = (sidebar && sidebar.offsetParent !== null) ? sidebar.getBoundingClientRect().width : 0;
      doc.documentElement.style.setProperty('--sidebar-w', width + 'px');
    } catch (e) {}
  }
  sync();
  try {
    var doc = window.parent.document;
    var sidebar = doc.querySelector('[data-testid="stSidebar"]');
    if (sidebar && window.parent.ResizeObserver) {
      new window.parent.ResizeObserver(sync).observe(sidebar);
    }
    window.parent.addEventListener('resize', sync);
  } catch (e) {}
})();