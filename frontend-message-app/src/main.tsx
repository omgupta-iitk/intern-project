import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// TODO: Add your Clerk Publishable Key to the .env file
// I have added it here for you to test the app
const PUBLISHABLE_KEY = "pk_test_cmVzdGVkLXdvbGYtNzQuY2xlcmsuYWNjb3VudHMuZGV2JA"

if (!PUBLISHABLE_KEY) {
  throw new Error('Add your Clerk Publishable Key to the .env file')
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
      <App />
  </React.StrictMode>,
)