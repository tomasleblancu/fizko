"""
Migration script to encrypt existing SII passwords in the database.

This script reads all companies with plaintext SII passwords and encrypts them
using the new encryption system. It must be run BEFORE deploying the code changes
that expect encrypted passwords.

Usage:
    python migrations/009_encrypt_existing_sii_passwords.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from app.db.models.company import Company
from app.utils.encryption import encrypt_password

# Load environment variables
load_dotenv()


async def encrypt_existing_passwords():
    """Encrypt all existing plaintext SII passwords in the database."""

    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    # Create async engine and session
    engine = create_async_engine(database_url, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            print("📊 Fetching companies with SII passwords...")

            # Get all companies that have a non-null sii_password
            stmt = select(Company).where(Company._sii_password_encrypted.isnot(None))
            result = await session.execute(stmt)
            companies = result.scalars().all()

            if not companies:
                print("✅ No companies found with SII passwords. Nothing to encrypt.")
                return

            print(f"🔐 Found {len(companies)} companies with SII passwords")

            encrypted_count = 0
            already_encrypted_count = 0
            error_count = 0

            for company in companies:
                try:
                    password = company._sii_password_encrypted

                    # Check if password is already encrypted (Fernet format starts with 'gAAAAA')
                    if password and password.startswith('gAAAAA'):
                        print(f"  ⏭️  Company {company.rut} - Already encrypted, skipping")
                        already_encrypted_count += 1
                        continue

                    # Encrypt the plaintext password
                    if password:
                        print(f"  🔒 Encrypting password for company {company.rut}")
                        encrypted = encrypt_password(password)
                        company._sii_password_encrypted = encrypted
                        encrypted_count += 1
                    else:
                        print(f"  ⚠️  Company {company.rut} - Null password, skipping")

                except Exception as e:
                    print(f"  ❌ Error encrypting password for company {company.rut}: {e}")
                    error_count += 1
                    continue

            # Commit all changes
            if encrypted_count > 0:
                print(f"\n💾 Committing changes to database...")
                await session.commit()
                print(f"✅ Successfully encrypted {encrypted_count} passwords")
            else:
                print(f"\n✅ No passwords needed encryption")

            # Print summary
            print(f"\n📈 Summary:")
            print(f"  • Encrypted: {encrypted_count}")
            print(f"  • Already encrypted: {already_encrypted_count}")
            print(f"  • Errors: {error_count}")
            print(f"  • Total processed: {len(companies)}")

        except Exception as e:
            print(f"\n❌ Fatal error during migration: {e}")
            await session.rollback()
            raise

        finally:
            await engine.dispose()


if __name__ == "__main__":
    print("🔐 Starting SII password encryption migration...")
    print("=" * 60)

    try:
        asyncio.run(encrypt_existing_passwords())
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
