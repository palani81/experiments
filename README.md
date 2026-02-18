# Experiments

**By Palani** — problem solver, tinkerer, and a firm believer that the best way to learn is to build.

This is my public playground for generative AI projects. I use AI as a collaborator to go from idea to working prototype — fast. Some of these are polished, some are held together with duct tape and curiosity. That's the point.

If something here sparks an idea or saves you time, that's a win.

## Projects

- **nas-explorer** — A self-hosted web app for browsing, searching, and organizing files on a Synology NAS. Built with FastAPI, React, and Docker. Features pure SMB access (no OS mounting needed), encrypted credential storage, multi-share management, full-text search, and media previews.

- **kidshield** — A parental control app for Android TV (Google TV, Fire TV) that locks the device to a kid-safe environment. Built with Kotlin, Jetpack Compose for TV, Hilt, and Room. Features kiosk mode via Device Owner or default launcher, PIN-protected parent dashboard, per-app daily time limits, age profiles (Toddler/Child/Teen), auto-discovery of installed TV apps, real-time usage tracking, and boot persistence.

- **learning-lab** — A self-hosted, expandable learning platform for kids to explore robotics and electronics. Ships with a 12-project Arduino curriculum (ages 9-12) progressing from blinking LEDs to building an autonomous obstacle-avoiding robot car. Features a gamified interactive web app with step-by-step wizard navigation, XP/progress tracking, and printable workbench project sheets. Designed for ELEGOO Mega Starter Kit and Smart Robot Car Kit V4. Deployable on Synology NAS (Docker/Web Station) or any local machine. Drop new collection folders to add topics like Python, 3D printing, etc.

- **car-combat** — Easy-drive car combat game variants with difficulty levels and power-ups.

- **firetv-beta-apps** — A Fire TV app for on-device management of beta apps published through Amazon Appstore's Live App Testing (LAT). Built with Kotlin and Android Leanback library for native Fire TV UI. Lets 3P developers browse, install, update, and uninstall beta builds directly from their Fire TV. Features D-pad-optimized browse and detail screens, real-time download progress, in-app purchase reset for testing, Login with Amazon SSO auth, and notification preferences. MVVM architecture with Repository pattern, mock API layer with comprehensive documentation for swapping to real Amazon Appstore APIs, and 89 unit tests.

## License

Projects in this repo are licensed under Apache 2.0 unless otherwise noted. See individual project folders for details.
