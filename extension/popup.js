document.getElementById('btn-trigger').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab && tab.id) {
    chrome.tabs.sendMessage(tab.id, { action: "TRIGGER_AUTOFILL" }, (response) => {
      if (chrome.runtime.lastError) {
        // If content script was not already loaded on this tab, inject it dynamically
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content.js']
        });
        chrome.scripting.insertCSS({
          target: { tabId: tab.id },
          files: ['content.css']
        });
      }
      window.close();
    });
  }
});

const STREAM_URLS = [
  "https://www.linkedin.com/search/results/content/?keywords=Java%20Backend%20Developer&sortBy=%22date_posted%22",
  "https://www.linkedin.com/search/results/content/?keywords=Java%20Developer&sortBy=%22date_posted%22",
  "https://www.linkedin.com/search/results/content/?keywords=Software%20Engineer%20Java&sortBy=%22date_posted%22"
];

document.getElementById('btn-linkedin-autohunt')?.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab && tab.url && tab.url.includes("linkedin.com")) {
    chrome.tabs.sendMessage(tab.id, { action: "START_LINKEDIN_HUNTER" });
    window.close();
  } else {
    chrome.tabs.create({ url: STREAM_URLS[0] });
    window.close();
  }
});

document.getElementById('btn-stream-java-backend')?.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab && tab.url && tab.url.includes("linkedin.com")) {
    chrome.tabs.sendMessage(tab.id, { action: "SWITCH_LINKEDIN_STREAM", streamIndex: 0 });
    window.close();
  } else {
    chrome.tabs.create({ url: STREAM_URLS[0] });
    window.close();
  }
});

document.getElementById('btn-stream-java-dev')?.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab && tab.url && tab.url.includes("linkedin.com")) {
    chrome.tabs.sendMessage(tab.id, { action: "SWITCH_LINKEDIN_STREAM", streamIndex: 1 });
    window.close();
  } else {
    chrome.tabs.create({ url: STREAM_URLS[1] });
    window.close();
  }
});

document.getElementById('btn-stream-software-eng')?.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab && tab.url && tab.url.includes("linkedin.com")) {
    chrome.tabs.sendMessage(tab.id, { action: "SWITCH_LINKEDIN_STREAM", streamIndex: 2 });
    window.close();
  } else {
    chrome.tabs.create({ url: STREAM_URLS[2] });
    window.close();
  }
});

