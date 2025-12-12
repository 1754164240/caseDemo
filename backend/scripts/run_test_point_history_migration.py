"""
Create the test_point_histories table (latest definition with code column).
"""
import sys

from scripts.run_migration import run_migration

SQL_FILE = "005_add_test_point_histories.sql"


def main():
    print("=" * 60)
    print("Running test point history migration")
    print("=" * 60)

    success = run_migration(SQL_FILE)
    print("\n" + "=" * 60)
    if not success:
        print("❌ Migration failed. Check the logs above for details.")
        sys.exit(1)

    print("✅ Migration finished successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
