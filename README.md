# LightShare V1.0 - Universal Cross-Platform App & SaaS

An ultra-modern, high-speed file transfer application engineered for **30GB+ transfers** over local Wi-Fi and mobile hotspots with **0 internet data usage**, available as native GUI apps for **Windows, Android, iOS, macOS, and Linux**.

- **App Package ID**: `com.lightshare.transfer.app`
- **Version**: `V1.0` (`1.0.0`)
- **Lead Developer**: Tanmaya Mahapatra (Alias: Retired AME)
- **Support & Contact**: `dronalabs.support@gmail.com`
- **Distribution**: Codester Digital Marketplace Edition

---

## Key Highlights & Features

| Feature | Description |
| :--- | :--- |
| **0 Data Usage (100% Offline)** | Transfer files entirely over local LAN / Personal Hotspot — 0 mobile data or internet consumed |
| **Up to 30GB+ Transfers** | High-throughput asynchronous 4MB streaming buffer bypasses RAM limits |
| **Custom User Profile** | Personalize your device name, avatar icon, and theme accent for transfers |
| **Filtered Category Picker** | Dedicated selection views for Photos, 4K Videos, Audio, Apps/APKs, Documents, and Archives |
| **Transfer History Log** | Chronological records of sent and received assets with live filters, speeds, and re-downloading |
| **Interactive User Guide** | Step-by-step onboarding guide for Wi-Fi, Hotspot, and In-App QR connection |
| **In-App Camera QR Scanner** | Point and scan host QR codes directly from inside the app browser view |
| **Live Speedometer & ETA** | Real-time `MB/s` bandwidth gauge, transferred bytes counter, and dynamic remaining time estimator |
| **Built-in Media Previews** | Image lightbox with zoom & swipe gestures, HTML5 video streaming player, and audio player |

---

## Supported App Formats & Platforms

| Platform | Formats Generated | Details |
| :--- | :--- | :--- |
| **Windows** | `LightShare-Setup.exe`, `LightShare-Setup.msi`, Portable `.exe` | Dedicated desktop GUI window, installer & MSI package |
| **Android** | `LightShare.apk` (Debug & Release), `.aab` | Native Android app with APK installer & PWA support (`com.lightshare.transfer.app`) |
| **iOS / iPadOS** | `.ipa`, `.xcarchive` | Native Apple Silicon iOS project & IPA export |
| **macOS** | `LightShare-AppleSilicon.dmg`, `.app` | Native Apple Silicon (M1/M2/M3/M4) installer |
| **Linux** | `.deb`, `.rpm`, `.AppImage`, `.snap` | Packages for Ubuntu, Debian, Fedora, RHEL, and Arch |

---

## Automated GitHub Actions Multi-Platform Build Pipeline

Every time you push this repository to GitHub or create a release tag (e.g. `v1.0.0`), the included **GitHub Actions Matrix Workflow** ([`.github/workflows/build-all-platforms.yml`](file:///c:/Users/jiten/Downloads/CODESTER%20PROJECT/ZeroConfig_Transfer_SaaS/.github/workflows/build-all-platforms.yml)) runs across **3 operating system runners** in parallel:

1. **Windows Runner (`windows-latest`)**: Builds `LightShare-Setup.exe` (NSIS) and `LightShare-Setup.msi`.
2. **Ubuntu Linux Runner (`ubuntu-latest`)**:
   - Compiles the Android `LightShare.apk` using Java 17 and Android Gradle.
   - Builds Linux `.deb`, `.rpm`, `.AppImage`, and `.snap` packages.
3. **macOS Runner (`macos-latest`)**:
   - Builds `LightShare-AppleSilicon.dmg` for Apple Silicon MacBooks/iMacs.
   - Prepares the iOS project and `.ipa` workspace.
4. **GitHub Releases Publisher**: Automatically gathers all 10 compiled binary files and publishes them in your GitHub repository's **Releases & Artifacts** tab for one-click downloading!

---

## Running Locally

### 1. Windows (Desktop GUI App)
- Double-click [`run.bat`](file:///c:/Users/jiten/Downloads/CODESTER%20PROJECT/ZeroConfig_Transfer_SaaS/run.bat) to launch the dedicated native Windows app window.
- Or run `python desktop_app.py`.

### 2. macOS & Linux
- Run [`./run.sh`](file:///c:/Users/jiten/Downloads/CODESTER%20PROJECT/ZeroConfig_Transfer_SaaS/run.sh) or `python3 desktop_app.py`.

### 3. Android (Termux / Standalone Host)
- Run `python -m app.main`.

---

## Hotspot Transfer Mode

Transfer files anywhere without a router or active internet connection:
- **Android Hotspot**: Auto-resolves to `http://192.168.43.1:53317`
- **iPhone Hotspot**: Auto-resolves to `http://172.20.10.1:53317`
- **Windows Hotspot**: Auto-resolves to `http://192.168.137.1:53317`

---

## Local Build Commands (For Developers)

```bash
# Install dependencies
npm install

# Build Windows .exe & .msi (from Windows)
npm run build:win

# Build Linux .deb, .rpm, .AppImage, .snap (from Linux)
npm run build:linux

# Build macOS Apple Silicon .dmg (from macOS)
npm run build:mac

# Build Android Project
npm run cap:android

# Build iOS Project
npm run cap:ios
```

---

## Author & License
- **Lead Developer**: Tanmaya Mahapatra (Alias: Retired AME)
- **License**: MIT License - Created for Codester Digital Marketplace.