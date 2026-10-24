# Google Cloud OAuth 2.0 & Gmail Integration Guide

This guide provides the exact step-by-step procedure to connect Gmail with **n8n** and **AgentMail AI**.

---

## 1. Create a Google Cloud Project

1. Navigate to the **[Google Cloud Console](https://console.cloud.google.com/)**.
2. Sign in with your standard Gmail account.
3. Click on the project dropdown at the top left and select **New Project**.
4. Set the project name to: `AgentMail-AI-Production` and click **Create**.
5. Once created, ensure `AgentMail-AI-Production` is selected in the project selector.

---

## 2. Enable the Gmail API

1. In the Google Cloud Console, open the navigation menu (≡) and select **APIs & Services > Library**.
2. In the search box, search for: `Gmail API`.
3. Click on the **Gmail API** tile and click the blue **Enable** button.

---

## 3. Configure the OAuth Consent Screen

1. In the left sidebar under *APIs & Services*, click **OAuth consent screen**.
2. Under **User Type**, choose **External** (unless you have a Google Workspace domain).
3. Click **Create**.
4. Fill in the required application details:
   - **App name**: `AgentMail AI`
   - **User support email**: *Select your Gmail address*
   - **Developer contact information**: *Your email address*
5. Click **Save and Continue**.
6. On the **Scopes** page:
   - Click **Add or Remove Scopes**.
   - Search for and check the following Gmail scopes:
     - `https://mail.google.com/` (Full access to read, compose, and send emails)
     - OR granular scopes: `gmail.readonly`, `gmail.send`, `gmail.modify`
   - Click **Update** then **Save and Continue**.
7. On the **Test Users** page:
   - Click **Add Users**.
   - Enter your personal Gmail address (e.g., `your_email@gmail.com`).
   - Click **Save and Continue**.

---

## 4. Create OAuth 2.0 Credentials

1. In the left sidebar, click **Credentials**.
2. Click **+ Create Credentials** at the top and select **OAuth client ID**.
3. Under **Application type**, select **Web application**.
4. Set the name to: `n8n Gmail OAuth Client`.
5. Under **Authorized redirect URIs**, click **+ Add URI** and paste the exact callback URI used by n8n:
   ```text
   http://localhost:5678/rest/oauth2-credential/callback
   ```
6. Click **Create**.
7. A modal will display:
   - **Client ID** (e.g., `1234567890-xxx.apps.googleusercontent.com`)
   - **Client Secret** (e.g., `GOCSPX-xxxxxx`)
   *(Keep this tab open or copy these to your private `.env` file. Never share them publicly).*

---

## 5. Connect Gmail to n8n

1. Open your local n8n instance at: **`http://localhost:5678`**.
2. In the bottom-left corner, click **Credentials > Add Credential**.
3. Search for: `Gmail OAuth2 API`.
4. Fill in:
   - **Client ID**: Paste your Client ID from Google Cloud.
   - **Client Secret**: Paste your Client Secret from Google Cloud.
5. Click **Connect my account**.
6. A Google sign-in window will open:
   - Choose your test Gmail account.
   - Click **Continue** (if Google warns that the app is unverified).
   - Grant permissions and click **Allow**.
7. Return to n8n. The credential status will show **Connected** with a green badge.
8. Click **Save**.

---

## 6. Safe Testing vs. Live Dispatch Mode

AgentMail AI is engineered with a **Safe Testing Gate**:

- When `TEST_MODE=true` in `.env`:
  - Incoming emails are processed through the complete AI pipeline (Classification, RAG, Memory, Planner, Critic).
  - When approved, instead of transmitting live emails to recruiters or contacts, the system logs:
    ```text
    [TEST_MODE ACTIVE] EMAIL WOULD BE SENT to recruiter@example.com | Subject: Re: Interview
    ```
- When `TEST_MODE=false`:
  - Live dispatch through Gmail API is enabled for approved drafts.

---

## 7. Troubleshooting Common OAuth Issues

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| `redirect_uri_mismatch` | Callback URL differs from Google Console | Verify `http://localhost:5678/rest/oauth2-credential/callback` is listed under Authorized Redirect URIs in Google Cloud Console. |
| `Access blocked: App has not completed verification` | App is in Testing status and user is not added | Add your Gmail address to **OAuth consent screen > Test users** in Google Cloud Console. |
| `Token expired or revoked` | Refresh token invalidated | In n8n credentials, click **Reconnect** and approve OAuth permissions again. |
