const { app, BrowserWindow, Tray, Menu, screen } = require("electron");
const path = require("path");

let mainWindow;
let tray;

function createWindow() {
  const { width: screenW, height: screenH } = screen.getPrimaryDisplay().workAreaSize;

  // Avatar window: bottom-right corner, transparent, always on top
  const winW = 420;
  const winH = 520;

  mainWindow = new BrowserWindow({
    width: winW,
    height: winH,
    x: screenW - winW - 20,
    y: screenH - winH - 20,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    skipTaskbar: false,
    hasShadow: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // In dev mode, load from Vite; in production, load built files
  const isDev = !app.isPackaged;
  if (isDev) {
    mainWindow.loadURL("http://localhost:5173");
  } else {
    mainWindow.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }

  // Enable click-through for transparent regions while allowing opaque areas to receive events
  // This allows the avatar to overlay other windows without blocking clicks on transparent areas
  mainWindow.setIgnoreMouseEvents(true, { forward: true });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function createTray() {
  // Use a simple icon for the tray
  tray = new Tray(path.join(__dirname, "icon.png"));

  const contextMenu = Menu.buildFromTemplate([
    {
      label: "Show Companion",
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      },
    },
    {
      label: "Hide Companion",
      click: () => {
        if (mainWindow) mainWindow.hide();
      },
    },
    { type: "separator" },
    {
      label: "Toggle Always on Top",
      type: "checkbox",
      checked: true,
      click: (item) => {
        if (mainWindow) mainWindow.setAlwaysOnTop(item.checked);
      },
    },
    { type: "separator" },
    {
      label: "Quit",
      click: () => {
        app.quit();
      },
    },
  ]);

  tray.setToolTip("Saathvik — Wellness Companion");
  tray.setContextMenu(contextMenu);

  tray.on("click", () => {
    if (mainWindow) {
      mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
    }
  });
}

app.whenReady().then(() => {
  createWindow();
  // Tray requires an icon file — skip if not available
  try {
    createTray();
  } catch (e) {
    console.log("Tray icon not found, skipping system tray:", e.message);
  }
});

app.on("window-all-closed", () => {
  app.quit();
});

app.on("activate", () => {
  if (!mainWindow) createWindow();
});
