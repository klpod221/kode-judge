from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from app.db.models import Language
from app.core.config import settings

SYNC_DATABASE_URL = str(settings.DATABASE_URL).replace("+asyncpg", "")
engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

LANGUAGES = [
    {
        "name": "Python",
        "version": "3.13",
        "file_name": "main",
        "file_extension": ".py",
        "compile_command": None,
        "run_command": "/usr/local/bin/python3 main.py",
    },
    {
        "name": "Node.js",
        "version": "20",
        "file_name": "main",
        "file_extension": ".js",
        "compile_command": None,
        "run_command": "/usr/bin/node --jitless main.js",
    },
    {
        "name": "C",
        "version": "gcc 12.2.0",
        "file_name": "main",
        "file_extension": ".c",
        "compile_command": "/usr/bin/gcc *.c -o main",
        "run_command": "./main",
    },
    {
        "name": "C++",
        "version": "g++ 12.2.0",
        "file_name": "main",
        "file_extension": ".cpp",
        "compile_command": "/usr/bin/g++ *.cpp -o main",
        "run_command": "./main",
    },
    {
        "name": "Java",
        "version": "openjdk 17",
        "file_name": "Main",
        "file_extension": ".java",
        "compile_command": "/usr/lib/jvm/java-17-openjdk-amd64/bin/javac Main.java",
        "run_command": "/usr/lib/jvm/java-17-openjdk-amd64/bin/java Main",
    },
]


def seed_languages():
    db = SessionLocal()
    try:
        print("Seeding languages...")
        for lang in LANGUAGES:
            existing_lang = db.query(Language).filter_by(name=lang["name"]).first()
            if not existing_lang:
                new_lang = Language(**lang)
                db.add(new_lang)
                print(f"Added language: {lang['name']}")
            else:
                for key, value in lang.items():
                    setattr(existing_lang, key, value)
                print(f"Updated language: {lang['name']}")
        db.commit()
        print("Seeding completed.")
    except Exception as e:
        db.rollback()
        print(f"Error occurred: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_languages()
