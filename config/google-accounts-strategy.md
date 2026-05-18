# 🔐 Google Accounts Strategy

> **Created:** 2026-05-18 14:30 EDT
> **Author:** Resource Adapter
> **Purpose:** Document the strategy for using multiple Google accounts for free cloud storage, NotebookLM, and ADC setup.

---

## Overview

MAD has multiple Google accounts. Each account provides:
- **15 GB free Google Drive storage**
- **Free NotebookLM access** (unlimited notebooks on free tier)
- **Free Google Colab** (GPU access for ML tasks)
- **Google Cloud free tier** ($300 credit for new accounts)
- **Firebase free tier** (hosting, auth, Firestore)

This strategy turns multiple accounts into a distributed, zero-cost cloud infrastructure.

---

## Account Allocation Plan

| Account | Purpose | Key Services |
|---------|---------|-------------|
| **Primary** (MAD's main) | Personal + main workspace | Drive, Gmail, Calendar |
| **Agent-Backups** | Agent memory + state backups | Drive API, Cloud Storage |
| **Research** | NotebookLM + research storage | NotebookLM, Drive, Colab |
| **Content-Farm** | Content archives + media storage | Drive, Photos, YouTube |
| **Quant-Lab** | Strategy data + backtest results | Drive, Sheets, BigQuery (free tier) |
| **Dev-Projects** | Code repos + deployment | Cloud Run, Firebase, Source Repositories |

---

## ADC (Application Default Credentials) Setup

ADC allows server-side applications to authenticate with Google APIs without user interaction. This is critical for automated agent backups.

### Per-Account Setup Process

#### Step 1: Create a Google Cloud Project
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (e.g., `agent-backups`, `research-storage`)
3. Enable required APIs:
   - Google Drive API
   - Google Sheets API (if needed)
   - Cloud Storage API (if needed)

#### Step 2: Create a Service Account
1. Navigate to **IAM & Admin → Service Accounts**
2. Create a service account (e.g., `agent-backup-sa`)
3. Grant minimal permissions (e.g., "Storage Object Creator" for Drive uploads)
4. Create a JSON key: **Keys → Add Key → Create New Key → JSON**
5. Download the JSON key file

#### Step 3: Store Credentials Securely
```
config/
  google-accounts/
    agent-backups/
      service-account.json    ← NEVER commit to git
      project-id.txt
    research/
      service-account.json
      project-id.txt
    content-farm/
      service-account.json
      project-id.txt
```

**CRITICAL:** Add `config/google-accounts/` to `.gitignore`. Never commit service account keys.

#### Step 4: Set Up ADC Environment
On the machine running agents:

```powershell
# Set ADC for a specific account
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\Users\wifik\Desktop\projects\larger-lab\config\google-accounts\agent-backups\service-account.json"

# Or use gcloud CLI
gcloud auth activate-service-account --key-file=config/google-accounts/agent-backups/service-account.json
gcloud config set project agent-backups-xxxxx
```

#### Step 5: Verify Access
```powershell
# Test Drive API access
pip install google-api-python-client google-auth
python -c "
from googleapiclient.discovery import build
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_file(
    'config/google-accounts/agent-backups/service-account.json',
    scopes=['https://www.googleapis.com/auth/drive.file']
)
service = build('drive', 'v3', credentials=creds)
results = service.files().list(pageSize=1).execute()
print('✅ Drive API access verified')
"
```

---

## NotebookLM Strategy

Each Google account gets free NotebookLM access. Use cases:

| Account | NotebookLM Use |
|---------|---------------|
| **Research** | Strategy research, market analysis, competitor intelligence |
| **Content-Farm** | Content research, trend analysis, topic clustering |
| **Quant-Lab** | Strategy documentation, backtest analysis, academic papers |
| **Dev-Projects** | Code documentation, architecture decisions, API references |

### NotebookLM API Access
NotebookLM doesn't have a public API yet, but you can:
1. Manually create notebooks per research topic
2. Upload source documents (PDFs, MD files, URLs)
3. Use the notebook for Q&A and summarization
4. Export summaries as markdown for agent consumption

**Future:** When NotebookLM API becomes available, automate notebook creation and querying.

---

## Storage Cost Analysis

| Resource | Free Tier | Our Need | Cost |
|----------|-----------|----------|------|
| Google Drive | 15 GB/account × N accounts | ~5 GB/account | **$0** |
| Google Colab | Free tier (GPU hours) | Occasional ML tasks | **$0** |
| Cloud Storage | 5 GB/month | Agent backups (~1 GB) | **$0** |
| Firebase Spark | Free tier | Static hosting, auth | **$0** |
| BigQuery | 1 TB queries/month | Backtest analysis | **$0** |
| **Total** | | | **$0/month** |

---

## Security Considerations

1. **Service account keys are secrets.** Store in `config/google-accounts/` (gitignored).
2. **Minimal permissions.** Each service account gets ONLY the permissions it needs.
3. **Separate projects per purpose.** If one account is compromised, others are unaffected.
4. **No personal data in service accounts.** Service accounts are for automated access only.
5. **Rotate keys quarterly.** Delete old keys, generate new ones.

---

## Implementation Timeline

| Step | Task | Owner | Status |
|------|------|-------|--------|
| 1 | MAD creates/identifies accounts for each purpose | MAD | ⏳ Pending |
| 2 | Create Google Cloud projects per account | MAD + RA | ⏳ Pending |
| 3 | Set up service accounts + download keys | RA | ⏳ Pending |
| 4 | Store credentials in config/google-accounts/ | RA | ⏳ Pending |
| 5 | Write backup scripts using Drive API | RA | ⏳ Pending |
| 6 | Test automated backup pipeline | RA | ⏳ Pending |
| 7 | Set up NotebookLM notebooks per system | RA | ⏳ Pending |

---

## What Needs MAD's Input

| Item | What's Needed |
|------|--------------|
| Account allocation | Which Google accounts to assign to which purposes |
| Account creation | Create new accounts if needed |
| Security review | Approve the service account permission model |
| Priority | Which account to set up first |

---

*Resource Adapter — Google Accounts Strategy — 2026-05-18 14:30 EDT*
