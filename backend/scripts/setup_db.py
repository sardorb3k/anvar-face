"""
Database setup script - initialize database with tables and sample data.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine, Base
from app.models import Student, StudentImage, Attendance


async def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    
    async with engine.begin() as conn:
        # Drop all tables (be careful in production!)
        await conn.run_sync(Base.metadata.drop_all)
        print("  ✓ Dropped existing tables")
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("  ✓ Created all tables")


async def create_indexes():
    """Create database indexes for better performance."""
    print("\nCreating database indexes...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_students_student_id ON students(student_id);",
        "CREATE INDEX IF NOT EXISTS idx_student_images_student_id ON student_images(student_id);",
        "CREATE INDEX IF NOT EXISTS idx_attendance_student_id ON attendance(student_id);",
        "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date);",
        "CREATE INDEX IF NOT EXISTS idx_attendance_created_at ON attendance(created_at);",
    ]
    
    async with engine.begin() as conn:
        for index_sql in indexes:
            await conn.execute(text(index_sql))
            print(f"  ✓ Created index")
    
    print("  ✓ All indexes created")


async def verify_setup():
    """Verify database setup."""
    print("\nVerifying database setup...")
    
    async with engine.begin() as conn:
        # Check if tables exist
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        
        tables = [row[0] for row in result]
        
        expected_tables = ['students', 'student_images', 'attendance']
        
        for table in expected_tables:
            if table in tables:
                print(f"  ✓ Table '{table}' exists")
            else:
                print(f"  ✗ Table '{table}' missing!")
                return False
    
    print("\n✓ Database setup verified successfully!")
    return True


async def main():
    """Main setup function."""
    print("="*60)
    print("DATABASE SETUP")
    print("="*60)
    print()
    
    try:
        # Create tables
        await create_tables()
        
        # Create indexes
        await create_indexes()
        
        # Verify setup
        success = await verify_setup()
        
        if success:
            print("\n" + "="*60)
            print("✓ DATABASE SETUP COMPLETE")
            print("="*60)
            return 0
        else:
            print("\n✗ Database setup failed!")
            return 1
            
    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        return 1
    finally:
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

