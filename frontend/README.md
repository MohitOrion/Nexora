# Nexora — React JS frontend

This is a plain React JS app built with Vite (not Next.js and not TypeScript).

## Run on your Mac
```bash
cd nexora-react-js
npm install
npm run dev
```
Open the local URL printed by Vite, usually http://localhost:5173.

## Pages
- Dashboard
- Explore opportunities, search and category filters
- Opportunity detail
- Saved opportunities
- Student profile
- Preferences/onboarding
- Login and signup UI

## Important
This is a frontend prototype. Opportunity data is sample/demo content, saved items and profile/preferences use browser localStorage, and login/signup are not connected to real authentication yet. The FastAPI API helper is in `src/api.js`; backend endpoints must be matched before connecting it.
