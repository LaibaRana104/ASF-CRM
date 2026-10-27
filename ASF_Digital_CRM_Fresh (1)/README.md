# ASF Digital Solutions CRM — Fresh Setup

Streamlit + Supabase CRM with light/dark appearance, high-contrast text, lead qualification, WhatsApp click-to-chat, search/filter, edit/delete, CSV import, CSV/Excel export.

## Create a new Supabase project
1. Open Supabase → SQL Editor → New query.
2. Paste all of `supabase_setup.sql` and Run.
3. Confirm `public.leads` exists in Table Editor.

## Create a new GitHub repository
Create a **private** repository (for example `ASF-Digital-CRM-Fresh`) and upload all files in this folder, including the `.streamlit` directory. The main file is `app.py`.

## Deploy to Streamlit Cloud
1. Create a new app and select your new repository, branch `main`, file `app.py`.
2. In App settings → Secrets, add:

```toml
APP_PASSWORD = "replace-with-a-strong-password"
SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"
SUPABASE_KEY = "YOUR_SERVER_SIDE_SUPABASE_KEY"
```

Keep these secrets private; never commit them to GitHub. Keep a server-side key on Streamlit only. Restrict app access and review data protection needs.

## WhatsApp limitation
The button opens WhatsApp with a pre-filled message. It does not automatically send or receive messages. Official automation requires Meta WhatsApp Cloud API and a webhook setup.
