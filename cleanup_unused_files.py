#!/usr/bin/env python3
"""
Clean up unused files in the app-laundry project
"""
import os
import shutil
from pathlib import Path

def identify_unused_files():
    """Identify potentially unused files"""
    
    root_dir = Path('.')
    unused_files = {
        'test_scripts': [],
        'migration_scripts': [],
        'markdown_docs': [],
        'debug_scripts': [],
        'temp_files': [],
        'backup_files': []
    }
    
    # Test scripts (temporary files used for development/testing)
    test_patterns = [
        'test_*.py',
        'debug_*.py',
        'check_*.py',
        'analyze_*.py',
        'comprehensive_test.py',
        'final_test.py',
        'final_validation.py',
        'validate_*.py',
        'verify_*.py'
    ]
    
    # Migration scripts (one-time use scripts)
    migration_patterns = [
        'migrate_*.py',
        'add_*.py',
        'setup_*.py',
        'init_db.py',
        'backfill_*.py',
        'simple_approval_migration.py',
        'create_database.py',
        'update_roles_migration.py'
    ]
    
    # Documentation files (development notes)
    doc_patterns = [
        '*_SUMMARY.md',
        '*_COMPLETE.md',
        '*_FIX.md',
        '*_FIXES_*.md',
        '*_IMPLEMENTATION.md',
        '*_FEATURE.md',
        '*_SUCCESS.md',
        '*_GUIDE.md',
        '*_STATUS.md',
        '*_READY.md',
        '*_ACHIEVEMENT.md'
    ]
    
    # Debug and demo scripts
    demo_patterns = [
        'demo_*.py',
        'create_sample_*.py',
        'create_notifications.py'
    ]
    
    # Get all Python files
    for pattern in test_patterns:
        for file in root_dir.glob(pattern):
            if file.is_file():
                unused_files['test_scripts'].append(str(file))
    
    for pattern in migration_patterns:
        for file in root_dir.glob(pattern):
            if file.is_file():
                unused_files['migration_scripts'].append(str(file))
    
    for pattern in doc_patterns:
        for file in root_dir.glob(pattern):
            if file.is_file():
                unused_files['markdown_docs'].append(str(file))
    
    for pattern in demo_patterns:
        for file in root_dir.glob(pattern):
            if file.is_file():
                unused_files['debug_scripts'].append(str(file))
    
    # Additional specific files
    specific_files = [
        'user_management.py',  # Duplicate of app/user_management.py
        'laundry.db',  # Database file in wrong location
        'fix_template.py',
        'analyze_template.py'
    ]
    
    for file in specific_files:
        if os.path.exists(file):
            unused_files['temp_files'].append(file)
    
    return unused_files

def display_cleanup_plan(unused_files):
    """Display what files will be cleaned up"""
    
    print("🧹 UNUSED FILE CLEANUP PLAN")
    print("=" * 50)
    
    total_files = 0
    
    for category, files in unused_files.items():
        if files:
            print(f"\n📁 {category.replace('_', ' ').title()} ({len(files)} files):")
            total_files += len(files)
            
            # Show first 10 files, then summarize
            for i, file in enumerate(files[:10]):
                print(f"   🗑️  {file}")
            
            if len(files) > 10:
                print(f"   ... and {len(files) - 10} more files")
    
    print(f"\n📊 TOTAL FILES TO CLEAN: {total_files}")
    
    return total_files

def cleanup_files(unused_files, confirm=True):
    """Clean up the identified unused files"""
    
    if confirm:
        response = input("\n❓ Do you want to proceed with cleanup? (y/N): ").lower().strip()
        if response != 'y':
            print("❌ Cleanup cancelled.")
            return False
    
    print("\n🧹 Starting cleanup...")
    
    cleaned_count = 0
    errors = []
    
    for category, files in unused_files.items():
        if files:
            print(f"\n📁 Cleaning {category.replace('_', ' ').title()}...")
            
            for file in files:
                try:
                    if os.path.exists(file):
                        os.remove(file)
                        print(f"   ✅ Deleted: {file}")
                        cleaned_count += 1
                    else:
                        print(f"   ⚠️  Not found: {file}")
                except Exception as e:
                    error_msg = f"❌ Failed to delete {file}: {str(e)}"
                    print(f"   {error_msg}")
                    errors.append(error_msg)
    
    print(f"\n🎉 CLEANUP COMPLETE!")
    print(f"   ✅ Files deleted: {cleaned_count}")
    if errors:
        print(f"   ❌ Errors: {len(errors)}")
        for error in errors:
            print(f"      {error}")
    
    return True

def keep_essential_files():
    """List essential files that should NOT be deleted"""
    
    essential_files = [
        'README.md',  # Main project documentation
        'requirements.txt',  # Dependencies
        'main.py',  # Application entry point
        '.env',  # Environment variables
        '.gitignore',  # Git configuration
        'pyproject.toml',  # Project configuration
        'app.yaml',  # Google Cloud configuration
    ]
    
    print("📋 ESSENTIAL FILES (WILL NOT BE DELETED):")
    for file in essential_files:
        if os.path.exists(file):
            print(f"   📄 {file}")
    
    return essential_files

def main():
    """Main cleanup function"""
    
    print("🧹 APP-LAUNDRY PROJECT CLEANUP")
    print("=" * 40)
    
    # Show essential files
    keep_essential_files()
    
    # Identify unused files
    unused_files = identify_unused_files()
    
    # Display cleanup plan
    total_files = display_cleanup_plan(unused_files)
    
    if total_files == 0:
        print("✨ No unused files found! Project is already clean.")
        return
    
    # Ask for confirmation and cleanup
    cleanup_files(unused_files, confirm=True)
    
    print("\n🎯 RECOMMENDED NEXT STEPS:")
    print("1. Review remaining files in the project")
    print("2. Test the application to ensure nothing is broken")
    print("3. Commit the cleaned-up project to git")
    print("4. Consider adding .gitignore rules to prevent future clutter")

if __name__ == "__main__":
    main()
