// JobApplyApp 1-Click Autofill Bookmarklet
// Drag this to your bookmarks bar or paste into Chrome DevTools console on Virtusa/Workday/Naukri!

javascript:(function(){
  if(window.__JOBAPPLY_INJECTED__){
    const fab = document.getElementById('jobapply-autofill-fab');
    if(fab){ fab.click(); return; }
  }
  const s = document.createElement('script');
  s.src = 'http://localhost:8000/extension/content.js?v=' + Date.now();
  const c = document.createElement('link');
  c.rel = 'stylesheet';
  c.href = 'http://localhost:8000/extension/content.css?v=' + Date.now();
  document.head.appendChild(c);
  document.body.appendChild(s);
  setTimeout(()=>{
    const fab = document.getElementById('jobapply-autofill-fab');
    if(fab) fab.click();
  }, 350);
})();
