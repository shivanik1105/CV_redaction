"""
List all available role chatbots

Usage: python chatbot/list_roles.py
"""

from pathlib import Path
import sys


def list_roles():
    """List all available role chatbots."""
    
    if getattr(sys, "frozen", False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent
    
    roles_dir = base_path / "roles"
    
    if not roles_dir.exists():
        print("📁 No roles directory found.")
        print(f"\nCreate your first role with:")
        print(f'  python chatbot/create_role_chatbot.py --name "Your Role Name"')
        return
    
    role_folders = [d for d in roles_dir.iterdir() if d.is_dir()]
    
    if not role_folders:
        print("📁 No role chatbots found.")
        print(f"\nCreate your first role with:")
        print(f'  python chatbot/create_role_chatbot.py --name "Your Role Name"')
        return
    
    print(f"\n🤖 Available Role Chatbots ({len(role_folders)}):\n")
    
    for role_folder in sorted(role_folders):
        role_name = role_folder.name
        
        # Check which files exist
        has_jd = (role_folder / "job_description.txt").exists()
        has_client = (role_folder / "client_info.txt").exists()
        has_faqs = (role_folder / "faqs.txt").exists()
        has_env = (role_folder / ".env").exists()
        
        # Calculate completeness
        files_present = sum([has_jd, has_client, has_faqs, has_env])
        completeness = (files_present / 4) * 100
        
        # Status indicator
        if completeness == 100:
            status = "✅"
        elif completeness >= 75:
            status = "⚠️"
        else:
            status = "❌"
        
        print(f"{status} {role_name}")
        print(f"   Completeness: {completeness:.0f}%")
        
        missing = []
        if not has_jd:
            missing.append("job_description.txt")
        if not has_client:
            missing.append("client_info.txt")
        if not has_faqs:
            missing.append("faqs.txt")
        if not has_env:
            missing.append(".env")
        
        if missing:
            print(f"   Missing: {', '.join(missing)}")
        
        # Show launch command
        print(f"   Launch: python chatbot/role_chatbot_template.py --role {role_name} --share")
        print()
    
    print("\n💡 Tips:")
    print("  • ✅ = Ready to launch")
    print("  • ⚠️ = Missing some files")
    print("  • ❌ = Incomplete setup")
    print()
    print("Create a new role:")
    print('  python chatbot/create_role_chatbot.py --name "Your Role Name"')


if __name__ == "__main__":
    list_roles()
