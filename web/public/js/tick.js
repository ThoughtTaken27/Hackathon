// A one-second clock that runs in a worker. Browsers slow down timers on a page you aren't looking at (Chrome: to once a
// minute after 5 minutes); a worker's timers keep their pace, so the kitchen screen keeps syncing while you use other tabs.
setInterval(() => postMessage(0), 1000);
