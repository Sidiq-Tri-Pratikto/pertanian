# Quickstart: Mobile shell

Needs Node 24 (`nvm use`) and a running API.

```bash
cd applications/hematdaya-mobile
make install
cp .env.example .env          # set EXPO_PUBLIC_API_URL if the API is not on port 8000
make web                      # or make run for Expo Go or a dev build
make check
make doctor
make export
```

A physical phone needs the computer's LAN address in `EXPO_PUBLIC_API_URL`. Expo Go only runs the current SDK, so use a development build once a newer SDK ships.
