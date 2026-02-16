# KidShield - Parental Control for Android TV

KidShield is a parental control app for Android TV (Google TV, Fire TV, etc.) that locks the device to a kid-safe environment. Children can only access parent-approved streaming apps with enforced daily time limits.

## Features

- **Kiosk Mode** - Home, Back, and Recent Apps buttons are blocked. Kids cannot exit to the launcher.
- **PIN-Protected Parent Access** - 4-6 digit PIN to access the Parent Dashboard.
- **Per-App Time Limits** - Set daily screen time limits for each app in 15-minute increments (15 min to 8 hours).
- **App Management** - Allow or block any installed TV app.
- **Age Profiles** - Toddler (2-5), Child (6-12), Teen (13-17), or No Filter. Automatically filters apps by age appropriateness.
- **Auto-Discovery** - Finds all installed TV apps automatically, not just a hardcoded list.
- **Usage Tracking** - Real-time per-app usage displayed on the Parent Dashboard.
- **Boot Persistence** - App auto-launches on device boot.

## Building

```bash
./gradlew assembleDebug
```

The APK will be at `app/build/outputs/apk/debug/app-debug.apk`.

## Installation on Google TV

### Step 1: Enable Developer Mode

1. On your Google TV, go to **Settings > System > About**
2. Scroll to **Android TV OS Build** and click it **7 times**
3. You'll see "You are now a developer"
4. Go back to **Settings > System > Developer options**
5. Enable **USB debugging**

### Step 2: Connect via ADB

**Option A - Wi-Fi (recommended for TVs):**

1. On the TV, go to **Settings > System > Developer options** and note the IP address
2. On your computer:
   ```bash
   adb connect <TV_IP_ADDRESS>:5555
   ```
3. Accept the connection prompt on the TV

**Option B - USB:**

Connect your computer to the TV via USB cable, then:
```bash
adb devices
```

### Step 3: Install KidShield

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

### Step 4: Set KidShield as Default Launcher (Recommended)

This makes the Home button return to KidShield instead of the stock launcher:

1. Launch KidShield and create your parent PIN
2. Go to **Parent Dashboard > gear icon > enter PIN**
3. If the red "Home Button Not Protected" banner appears, click it
4. Select **KidShield** from the launcher list
5. Choose **"Always"**

Now pressing Home will always return to KidShield.

### Step 5 (Optional): Full Kiosk Mode via Device Owner

For the strongest protection (blocks Home, Recent Apps, status bar, notifications), set KidShield as Device Owner. This blocks ALL escape routes.

**Requirement:** The device must have **no Google account** added. Either do this during initial setup (skip sign-in) or remove accounts first.

```bash
adb shell dpm set-device-owner com.kidshield.tv/.service.KidShieldDeviceAdminReceiver
```

Then launch the app:
```bash
adb shell am start -n com.kidshield.tv/.MainActivity
```

To remove Device Owner later:
```bash
adb shell dpm remove-active-admin com.kidshield.tv/.service.KidShieldDeviceAdminReceiver
```

## Installation on Amazon Fire TV

### Step 1: Enable Developer Mode

1. Go to **Settings > My Fire TV > About**
2. Click the **serial number 7 times** to enable Developer Options
3. Go back to **Settings > My Fire TV > Developer Options**
4. Enable **ADB debugging**
5. Enable **Apps from Unknown Sources**

### Step 2: Connect via ADB

Fire TV only supports Wi-Fi ADB:

1. Go to **Settings > My Fire TV > About > Network** to find the IP address
2. On your computer:
   ```bash
   adb connect <FIRE_TV_IP>:5555
   ```
3. Accept the prompt on the Fire TV screen

### Step 3: Install KidShield

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

### Step 4: Set as Default Launcher

Same as Google TV Step 4 above - open Parent Dashboard and click the "Home Button Not Protected" banner to set KidShield as the default launcher.

### Step 5 (Optional): Device Owner for Full Kiosk Mode

```bash
adb shell dpm set-device-owner com.kidshield.tv/.service.KidShieldDeviceAdminReceiver
```

**Note:** Some Fire TV devices restrict this command. If it fails, try removing all accounts first:
```bash
adb shell pm list users
```

## Protection Levels

| Feature | Default Launcher | Device Owner |
|---|---|---|
| Home button returns to KidShield | Yes | Yes (blocked entirely) |
| Back button blocked | Yes | Yes |
| Recent Apps blocked | No | Yes |
| Status bar / notifications blocked | No | Yes |
| Requires factory reset | No | Sometimes* |
| Requires ADB | No (set via UI) | Yes (one-time) |

*Device Owner requires no accounts on the device. On a new device, skip sign-in first. On an existing device, you may need to remove accounts.

## Parent Dashboard

Access via the **gear icon** on the Kid Home Screen, then enter your PIN.

- **Time Limits** - View and adjust per-app daily limits
- **Manage Apps** - Allow or block installed apps
- **Content Safety** - Set age profile (Toddler/Child/Teen/No Filter)
- **Setup Wizard** - Guided setup for streaming app parental controls
- **Per-App Usage** - Click any app row to adjust its time limit

## Architecture

- **Language:** Kotlin
- **UI:** Jetpack Compose for TV (`androidx.tv:tv-material`)
- **Architecture:** MVVM + Clean Architecture
- **DI:** Hilt
- **Database:** Room (app configs, time limits, usage logs)
- **Security:** Bcrypt PIN hashing + EncryptedSharedPreferences
- **Navigation:** D-pad optimized with focus management

## Project Structure

```
com.kidshield.tv/
  MainActivity.kt              # Entry point, lock task management
  KidShieldApp.kt              # Hilt application
  data/
    local/db/                   # Room database, DAOs, entities
    repository/                 # App, Usage repositories
    KnownStreamingApps.kt      # Known streaming app registry
  domain/
    model/                      # Domain models
    usecase/                    # Business logic
  service/
    LockTaskHelper.kt          # Device Owner + lock task management
    KidShieldDeviceAdminReceiver.kt
    AppMonitorService.kt        # Foreground service for usage tracking
    BootReceiver.kt             # Auto-launch on boot
  ui/
    kid/home/                   # Kid-facing home screen
    kid/timesup/                # Time's up screen
    parent/dashboard/           # Parent Dashboard
    parent/timelimits/          # Time limit screens
    parent/appmanagement/       # App allow/block management
    parent/contentsafety/       # Age profile selection
    parent/setupwizard/         # Guided setup
    parent/pin/                 # PIN entry/creation
    navigation/                 # Nav graph + routes
    theme/                      # Colors, typography
```
