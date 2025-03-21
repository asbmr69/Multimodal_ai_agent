import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_dir():
    """Clean build directories"""
    dirs_to_clean = ['build', 'dist', 'ai_agent_app.egg-info']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name}...")
            shutil.rmtree(dir_name)

def install_requirements():
    """Install required packages"""
    print("Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def run_pyinstaller():
    """Build executable with PyInstaller"""
    print("Building executable with PyInstaller...")
    
    # Create spec file if it doesn't exist
    if not os.path.exists("ai_agent_app.spec"):
        subprocess.check_call([
            sys.executable, 
            "-m", 
            "PyInstaller",
            "--name=AI_Agent_Desktop",
            "--windowed",
            "--icon=app/resources/icon.ico",
            "--add-data=app/resources;resources",
            "main.py"
        ])
    else:
        # Use existing spec file
        subprocess.check_call([
            sys.executable, 
            "-m", 
            "PyInstaller",
            "ai_agent_app.spec"
        ])

def copy_additional_files():
    """Copy additional files to dist directory"""
    print("Copying additional files...")
    
    dist_dir = Path("dist") / "AI_Agent_Desktop"
    
    # Create directories
    plugins_dir = dist_dir / "plugins"
    plugins_dir.mkdir(exist_ok=True)
    
    # Copy plugin manifest
    shutil.copy("plugins/plugin_manifest.json", plugins_dir)
    
    # Copy documentation
    if os.path.exists("docs"):
        shutil.copytree("docs", dist_dir / "docs")
    
    # Copy default configuration
    shutil.copy("default_config.json", dist_dir)

def create_installer():
    """Create Windows installer with NSIS"""
    print("Creating Windows installer...")
    
    # Check if NSIS is installed
    nsis_path = "C:\\Program Files (x86)\\NSIS\\makensis.exe"
    if not os.path.exists(nsis_path):
        print("NSIS not found. Please install NSIS to create an installer.")
        return
    
    # Run NSIS script
    subprocess.check_call([
        nsis_path,
        "installer.nsi"
    ])

def main():
    """Main build function"""
    print("Starting build process...")
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Build AI Agent Desktop application')
    parser.add_argument('--clean', action='store_true', help='Clean build directories')
    parser.add_argument('--installer', action='store_true', help='Create Windows installer')
    args = parser.parse_args()
    
    if args.clean:
        clean_build_dir()
    
    install_requirements()
    run_pyinstaller()
    copy_additional_files()
    
    if args.installer:
        create_installer()
    
    print("Build completed successfully!")

if __name__ == "__main__":
    main()