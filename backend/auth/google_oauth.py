from fastapi import APIRouter, Depends, HTTPException, status
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from pydantic import BaseModel
import json
import os
import io
import mimetypes
import httpx
from pathlib import Path
from datetime import datetime

from .auth import get_current_user, User

router = APIRouter(tags=["google-oauth"])

GOOGLE_OAUTH_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
]

USER_TOKENS_FILE = Path(__file__).parent.parent / "data" / "user_google_tokens.json"
MATERIALS_DIR = Path(os.getenv("MATERIALS_DIR", Path(__file__).parent.parent / "data" / "materials"))


def load_user_tokens() -> dict:
    if USER_TOKENS_FILE.exists():
        with open(USER_TOKENS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_user_tokens(tokens: dict):
    USER_TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USER_TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=2, default=str)


def build_flow(redirect_uri: str) -> Flow:
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth não configurado. Adicione GOOGLE_OAUTH_CLIENT_ID e GOOGLE_OAUTH_CLIENT_SECRET ao .env",
        )
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=GOOGLE_OAUTH_SCOPES,
        redirect_uri=redirect_uri,
    )


def get_credentials_for_user(username: str) -> Credentials:
    tokens = load_user_tokens()
    user_token = tokens.get(username)
    if not user_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Drive pessoal não conectado. Conecte primeiro.",
        )
    creds = Credentials(
        token=user_token["token"],
        refresh_token=user_token.get("refresh_token"),
        token_uri=user_token.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=user_token.get("client_id", GOOGLE_OAUTH_CLIENT_ID),
        client_secret=user_token.get("client_secret", GOOGLE_OAUTH_CLIENT_SECRET),
        scopes=user_token.get("scopes", GOOGLE_OAUTH_SCOPES),
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        tokens[username]["token"] = creds.token
        save_user_tokens(tokens)
    return creds


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/auth/google")
async def get_google_auth_url(
    redirect_uri: str,
    current_user: User = Depends(get_current_user),
):
    flow = build_flow(redirect_uri)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return {"auth_url": auth_url}


class ExchangeCodeRequest(BaseModel):
    code: str
    redirect_uri: str


@router.post("/auth/google/exchange")
async def exchange_google_code(
    body: ExchangeCodeRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        flow = build_flow(body.redirect_uri)
        flow.fetch_token(code=body.code)
        creds = flow.credentials

        # Fetch Google account email
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {creds.token}"},
            )
        google_email = resp.json().get("email", "") if resp.is_success else ""

        tokens = load_user_tokens()
        tokens[current_user.username] = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes) if creds.scopes else GOOGLE_OAUTH_SCOPES,
            "google_email": google_email,
            "connected_at": datetime.utcnow().isoformat(),
        }
        save_user_tokens(tokens)

        return {
            "success": True,
            "message": f"Drive pessoal conectado! ({google_email})",
            "google_email": google_email,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao trocar código OAuth: {str(e)}",
        )


@router.get("/auth/google/status")
async def get_google_status(current_user: User = Depends(get_current_user)):
    tokens = load_user_tokens()
    user_token = tokens.get(current_user.username)
    if not user_token:
        return {"connected": False}
    return {
        "connected": True,
        "google_email": user_token.get("google_email", ""),
        "connected_at": user_token.get("connected_at", ""),
    }


@router.delete("/auth/google/disconnect")
async def disconnect_google(current_user: User = Depends(get_current_user)):
    tokens = load_user_tokens()
    tokens.pop(current_user.username, None)
    save_user_tokens(tokens)
    return {"success": True, "message": "Drive pessoal desconectado."}


# ─── Private Drive Sync ───────────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".pptx", ".xlsx", ".csv", ".mp4", ".mp3"}
DRIVE_FILE_EXPORT_MAP = {
    "application/vnd.google-apps.document": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
    "application/vnd.google-apps.spreadsheet": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"),
    "application/vnd.google-apps.presentation": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", ".pptx"),
}


class PrivateSyncRequest(BaseModel):
    folder_id: str
    download_files: bool = True
    subfolder: str = "Drive Privado"


@router.post("/drive/private-sync")
async def sync_private_drive(
    body: PrivateSyncRequest,
    current_user: User = Depends(get_current_user),
):
    creds = get_credentials_for_user(current_user.username)

    try:
        from googleapiclient.discovery import build
        service = build("drive", "v3", credentials=creds)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao conectar ao Drive: {e}")

    dest_dir = MATERIALS_DIR / body.subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)

    stats = {"listed": 0, "downloaded": 0, "skipped": 0, "errors": 0, "files": []}

    def list_files(folder_id: str):
        page_token = None
        while True:
            resp = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="nextPageToken, files(id, name, mimeType, size)",
                pageToken=page_token,
                pageSize=100,
            ).execute()
            for f in resp.get("files", []):
                yield f
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

    def download_file(file_meta: dict) -> bool:
        name = file_meta["name"]
        mime = file_meta["mimeType"]
        fid = file_meta["id"]

        if mime in DRIVE_FILE_EXPORT_MAP:
            export_mime, ext = DRIVE_FILE_EXPORT_MAP[mime]
            stem = Path(name).stem
            dest = dest_dir / f"{stem}{ext}"
            if dest.exists():
                return False  # skip
            req = service.files().export_media(fileId=fid, mimeType=export_mime)
            data = req.execute()
        else:
            ext = Path(name).suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                return False
            dest = dest_dir / name
            if dest.exists():
                return False
            req = service.files().get_media(fileId=fid)
            data = req.execute()

        dest.write_bytes(data)
        return True

    for file_meta in list_files(body.folder_id):
        stats["listed"] += 1
        if not body.download_files:
            stats["files"].append({"name": file_meta["name"], "type": file_meta["mimeType"]})
            continue
        try:
            downloaded = download_file(file_meta)
            if downloaded:
                stats["downloaded"] += 1
                stats["files"].append({"name": file_meta["name"], "status": "downloaded"})
            else:
                stats["skipped"] += 1
        except Exception as e:
            stats["errors"] += 1
            stats["files"].append({"name": file_meta["name"], "status": "error", "error": str(e)})

    return {
        "status": "success",
        "message": f"Sincronização concluída: {stats['downloaded']} baixados, {stats['skipped']} ignorados, {stats['errors']} erros.",
        "statistics": stats,
        "destination": str(dest_dir),
    }
