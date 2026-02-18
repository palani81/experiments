# Experiments

**By Palani** — problem solver, tinkerer, and a firm believer that the best way to learn is to build.

This is my public playground for generative AI projects. I use AI as a collaborator to go from idea to working prototype — fast. Some of these are polished, some are held together with duct tape and curiosity. That's the point.

If something here sparks an idea or saves you time, that's a win.

## Projects

- **nas-explorer** — A self-hosted web app for browsing, searching, and organizing files on a Synology NAS. Built with FastAPI, React, and Docker. Features pure SMB access (no OS mounting needed), encrypted credential storage, multi-share management, full-text search, and media previews.

- **kidshield** — A parental control app for Android TV (Google TV, Fire TV) that locks the device to a kid-safe environment. Built with Kotlin, Jetpack Compose for TV, Hilt, and Room. Features kiosk mode via Device Owner or default launcher, PIN-protected parent dashboard, per-app daily time limits, age profiles (Toddler/Child/Teen), auto-discovery of installed TV apps, real-time usage tracking, and boot persistence.

- **learning-lab** — A self-hosted, expandable learning platform for kids to explore robotics and electronics. Ships with a 12-project Arduino curriculum (ages 9-12) progressing from blinking LEDs to building an autonomous obstacle-avoiding robot car. Features a gamified interactive web app with step-by-step wizard navigation, XP/progress tracking, and printable workbench project sheets. Designed for ELEGOO Mega Starter Kit and Smart Robot Car Kit V4. Deployable on Synology NAS (Docker/Web Station) or any local machine. Drop new collection folders to add topics like Python, 3D printing, etc.

- **fire-tv-beta-manager** — An on-device beta app management tool for Amazon Appstore's Live App Testing (LAT) program. Built with React Native (TypeScript) targeting Fire TV / Android TV. Lets 3P developers' beta testers browse, download, update, and manage beta apps directly from their Fire TV. Features invite-based device enrollment, D-pad-optimized UI with focus animations matching Fire TV's native aesthetic, live download progress tracking, push notification support, and in-app purchase reset for testing. Clean architecture with Zustand + Redux Toolkit state management, mock API layer with swappable interfaces ready for real Amazon Appstore API integration, dual-layer caching, and full test coverage.

## License

Projects in this repo are licensed under Apache 2.0 unless otherwise noted. See individual project folders for details.
