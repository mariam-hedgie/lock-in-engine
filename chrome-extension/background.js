// Lock-In Engine — Chrome extension background service worker
// Watches for tab switches and URL changes, reports domain to local Python app.

const SERVER = "http://127.0.0.1:27182";

// Debounce: don't spam the server on rapid tab switches
let debounceTimer = null;
let lastDomain = "";

function domainFromUrl(url) {
  try {
    const u = new URL(url);
    // Strip leading www. for cleaner log output
    return u.hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

function report(url) {
  const domain = domainFromUrl(url);

  // Skip browser internal pages (new tab, settings, extensions etc.)
  if (!domain || url.startsWith("chrome://") || url.startsWith("chrome-extension://")) {
    return;
  }

  // Skip if same domain as last report (e.g. navigating within instagram.com)
  // Remove this check if you want per-page-load granularity
  if (domain === lastDomain) return;
  lastDomain = domain;

  // Debounce 800ms so fast tab-switching doesn't flood the server
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    fetch(SERVER, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, domain }),
    }).catch(() => {
      // Python app not running — silently ignore
    });
  }, 800);
}

// Tab switched to a different tab
chrome.tabs.onActivated.addListener(({ tabId }) => {
  chrome.tabs.get(tabId, (tab) => {
    if (tab && tab.url) report(tab.url);
  });
});

// URL changed within the current tab (navigation, back/forward)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Only fire when the URL actually changes and the tab is active
  if (changeInfo.url && tab.active) {
    report(changeInfo.url);
  }
});

// Window focus changed (switched browser windows)
chrome.windows.onFocusChanged.addListener((windowId) => {
  if (windowId === chrome.windows.WINDOW_ID_NONE) return;
  chrome.tabs.query({ active: true, windowId }, (tabs) => {
    if (tabs[0] && tabs[0].url) report(tabs[0].url);
  });
});
