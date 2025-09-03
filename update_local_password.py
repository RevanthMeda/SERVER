#!/usr/bin/env python3
"""
Local Password Update Script for Windows
Updates your local .env file with the new Gmail app password
"""

import os
import shutil
from datetime import datetime

def update_local_env_file():
    """Update the local .env file with new password"""
    
    print("🔧 Updating Local Environment File...")
    
    env_file = '.env'
    backup_file = f'.env.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    # Check if .env exists
    if not os.path.exists(env_file):
        print(f"❌ .env file not found at {os.path.abspath(env_file)}")
        return False
    
    # Create backup
    print(f"📋 Creating backup: {backup_file}")
    shutil.copy(env_file, backup_file)
    
    # Read current file
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update password lines
    new_lines = []
    password_updated = False
    
    for line in lines:
        if line.startswith('SMTP_PASSWORD='):
            old_password = line.split('=')[1].strip()
            print(f"🔍 Found old password: {old_password[:4]}...{old_password[-4:]}")
            new_lines.append('SMTP_PASSWORD=rleg tbhv rwvb kdus\n')
            password_updated = True
            print(f"✅ Updated to new password: rleg...kdus")
        else:
            new_lines.append(line)
    
    # Write updated file
    with open(env_file, 'w') as f:
        f.writelines(new_lines)
    
    if password_updated:
        print("✅ Local .env file updated successfully!")
        print(f"💾 Backup saved as: {backup_file}")
        return True
    else:
        print("⚠️  SMTP_PASSWORD not found in .env file")
        return False

def test_local_credentials():
    """Test the updated credentials"""
    print("\n🧪 Testing Updated Credentials...")
    
    try:
        # Force reload environment
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        smtp_password = os.environ.get('SMTP_PASSWORD', '')
        smtp_username = os.environ.get('SMTP_USERNAME', '')
        
        print(f"📧 Username: {smtp_username}")
        print(f"🔐 Password: {smtp_password[:4]}...{smtp_password[-4:]} (Length: {len(smtp_password)})")
        
        if smtp_password == 'rleg tbhv rwvb kdus':
            print("✅ Password correctly updated!")
            return True
        else:
            print("❌ Password not updated correctly")
            return False
            
    except Exception as e:
        print(f"❌ Error testing credentials: {e}")
        return False

def clear_python_cache():
    """Clear Python cache files"""
    print("\n🧹 Clearing Python Cache...")
    
    import sys
    import gc
    
    # Clear module cache
    modules_to_clear = ['config', 'utils', 'auth']
    for module in modules_to_clear:
        if module in sys.modules:
            print(f"   🗑️  Clearing {module}")
            del sys.modules[module]
    
    # Force garbage collection
    collected = gc.collect()
    print(f"   ♻️  Garbage collected: {collected} objects")
    
    print("✅ Cache cleared!")

if __name__ == "__main__":
    print("🚀 Local Windows Environment Update")
    print("=" * 40)
    
    # Step 1: Update .env file
    if update_local_env_file():
        # Step 2: Clear cache
        clear_python_cache()
        
        # Step 3: Test credentials
        if test_local_credentials():
            print("\n🎉 SUCCESS! Your local environment is updated!")
            print("\n📝 Next Steps:")
            print("1. Restart your application (Ctrl+C then python app.py)")
            print("2. The new password will be loaded automatically")
            print("3. Email notifications should work properly")
        else:
            print("\n❌ Update failed. Please check the output above.")
    else:
        print("\n❌ Failed to update .env file. Please check the output above.")