/**
 * ZYRA / FRIDAY Browser Bridge Extension - Background Service Worker
 * Communicates with local ZYRA assistant on http://127.0.0.1:5005/browser/bridge
 */

const BRIDGE_URL = "http://127.0.0.1:5005/browser/bridge";

// Collect open tabs and sync with ZYRA
async function syncTabsWithZyra() {
  try {
    const tabs = await chrome.tabs.query({});
    const simplifiedTabs = tabs.map(t => ({
      id: t.id,
      title: t.title || "Untitled",
      url: t.url || "",
      active: t.active,
      windowId: t.windowId
    }));

    const response = await fetch(BRIDGE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "sync_tabs",
        tabs: simplifiedTabs
      })
    });

    if (response.ok) {
      const data = await response.json();
      if (data && data.pending_command) {
        handleBridgeCommand(data.pending_command);
      }
    }
  } catch (err) {
    // ZYRA assistant server may be offline or not running yet
  }
}

// Execute command received from ZYRA
async function handleBridgeCommand(cmd) {
  if (!cmd || !cmd.action) return;

  switch (cmd.action) {
    case "switch_tab":
      if (cmd.tabId) {
        chrome.tabs.update(cmd.tabId, { active: true });
        if (cmd.windowId) chrome.windows.update(cmd.windowId, { focused: true });
      }
      break;

    case "close_tab":
      if (cmd.tabId) {
        chrome.tabs.remove(cmd.tabId);
      }
      break;

    case "open_tab":
      if (cmd.url) {
        chrome.tabs.create({ url: cmd.url });
      }
      break;
  }
}

// Poll sync every 3 seconds
setInterval(syncTabsWithZyra, 3000);

// Also sync immediately on tab events
chrome.tabs.onCreated.addListener(syncTabsWithZyra);
chrome.tabs.onRemoved.addListener(syncTabsWithZyra);
chrome.tabs.onUpdated.addListener(syncTabsWithZyra);
chrome.tabs.onActivated.addListener(syncTabsWithZyra);
