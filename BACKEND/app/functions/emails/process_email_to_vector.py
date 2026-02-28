from sqlalchemy.orm import Session
from app.memory.models import EmailEmbedding
from app.db.models.user_model import UserEmails
from app.db.session import engine
from sqlalchemy import select, func
from app.db.models.user_model import User
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import base64, os
from app.services.llm import update_user_identity_gemini
from app.core.config import settings
from fastapi import BackgroundTasks
from app.db.session import async_session_maker


async def process_email_to_vector(db: Session, email: UserEmails):
    chunks = [email.body_plain[i:i+500] for i in range(0, len(email.body_plain), 400)]

    for chunk in chunks:
        vector = engine.generate(chunk)
        
        new_embedding = EmailEmbedding(
            email_id=email.id,
            user_id=email.user_id,
            embedding=vector,
            content_chunk=chunk,
            is_sent_by_user=email.is_sent_by_user
        )
        db.add(new_embedding)

    email.is_processed = True
    db.commit()


async def scan_user_emails(background_tasks: BackgroundTasks, user_id: int):
    from app.db.session import async_session_maker
    async with async_session_maker() as db:
    # 1. Get user and tokens
        user = await db.get(User, user_id)
        
        # 2. Reconstruct credentials
        creds = Credentials(
            token=user.google_access_token,
            refresh_token=user.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET
        )

        # 3. Build Gmail Service
        service = build('gmail', 'v1', credentials=creds)
        
        # 4. List messages (Example: last 100)
        results = service.users().messages().list(userId='me', maxResults=200, q="is:sent").execute()
        messages = results.get('messages', [])

        for msg in messages:
            msg_id = msg['id']
            exists_stmt = select(UserEmails).where(UserEmails.message_id == msg_id)
            exists_result = await db.execute(exists_stmt)
            if exists_result.scalars().first():
                continue
            # 5. Fetch Full Message Detail
            detail = service.users().messages().get(userId='me', id=msg_id).execute()
            body = ""
            payload = detail.get('payload', {})
            labels = detail.get('labelIds', [])
            is_sent = "SENT" in labels
            if "SENT" not in labels:
                continue
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                data = payload.get('body', {}).get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
            # Fallback to snippet if body is empty
            final_text = body if body else detail.get('snippet')
            new_email = UserEmails(
                user_id=user_id,
                message_id=msg_id,
                subject=next((h['value'] for h in payload['headers'] if h['name'].lower() == 'subject'), "No Subject"),
                sender=next((h['value'] for h in payload['headers'] if h['name'].lower() == 'from'), "Unknown"),
                body_plain=final_text,
                is_sent_by_user=is_sent,
                received_at=datetime.now(timezone.utc)
            )
            db.add(new_email)
        await db.commit()
        # 7. AUTOMATIC TRIGGER CHECK
        # Check how many emails are waiting to be analyzed
        count_stmt = select(func.count()).select_from(UserEmails).where(
            UserEmails.user_id == user_id,
            UserEmails.is_processed == False
        )
        result = await db.execute(count_stmt)
        un_analyzed_count = result.scalar()
        if un_analyzed_count >= 10:
            print(f"Triggering automatic analysis for User {user_id} ({un_analyzed_count} emails pending)")
            # We use background_tasks so the scanner can finish 
            # while the AI starts the heavy thinking
            background_tasks.add_task(update_user_identity_profile, user_id)

async def update_user_identity_profile(user_id: int):
    # 1. Start a fresh database session
    async with async_session_maker() as db:
        # 2. Get the user so we can get their email address
        user = await db.get(User, user_id)
        if not user:
            print(f"User {user_id} not found")
            return

        # 3. ENSURE DIRECTORIES EXIST
        # This creates 'memories/email_profiles/' if they don't exist
        folder_path = "memories/email_profiles"
        os.makedirs(folder_path, exist_ok=True)

        # 4. Define filename using user's email
        # We replace '@' and '.' to keep the filename clean
        safe_email = user.email.replace("@", "_at_").replace(".", "_")
        file_path = f"{folder_path}/{safe_email}.md"
        while True:
            # 5. Fetch the emails to process
            stmt = select(UserEmails).where(
                UserEmails.user_id == user_id,
                UserEmails.is_processed == False
            ).limit(20)
            
            result = await db.execute(stmt)
            new_emails = result.scalars().all()
            
            if not new_emails:
                print(f"All emails for {user.email} have been analyzed. Closing task.")
                return

            # 6. Read existing profile if it exists
            existing_profile = ""
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    existing_profile = f.read()

            # 7. Format emails for Gemini
            email_payload = "\n\n".join([
                f"Subject: {e.subject}\nBody: {e.body_plain}" for e in new_emails
            ])

            # 8. Call Gemini (make sure this is imported!)
            new_profile_content = await update_user_identity_gemini(existing_profile, email_payload)

            if new_profile_content:
                # 9. SAVE THE FILE (This will now work because of os.makedirs)
                with open(file_path, "w") as f:
                    f.write(new_profile_content)

                # 10. Mark emails as processed
                for e in new_emails:
                    e.is_processed = True
                await db.commit()
                print(f"Profile updated for {user.email}")