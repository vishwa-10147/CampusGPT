# ==============================================================================
# CampusGPT Backend — Grant or Revoke Admin
# ==============================================================================
"""Give an existing account admin rights (or take them away).

Admins can see every document, delete any document, and share uploads with
everyone. The account must already exist; promoting also marks its email as
verified so the admin can sign in straight away.

    docker compose exec backend python scripts/make_admin.py someone@college.edu
    docker compose exec backend python scripts/make_admin.py someone@college.edu --revoke
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import async_session_maker, close_db
from app.repositories.user_repo import UserRepository


async def main(email: str, revoke: bool) -> int:
    try:
        async with async_session_maker() as session:
            user = await UserRepository(session).get_by_email(email)
            if not user:
                print(f"No account with email {email}. Register it first.")
                return 1
            user.is_admin = not revoke
            if not revoke:
                user.email_verified = True
            await session.commit()
            print(f"{email} is {'no longer' if revoke else 'now'} an admin")
            return 0
    finally:
        await close_db()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("email")
    parser.add_argument("--revoke", action="store_true", help="remove admin rights instead")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.email, args.revoke)))
