import os
import json
from pathlib import Path
from datetime import datetime
import subprocess

def analyze_project_structure(root_path):
    """
    Analyze the project structure and generate a comprehensive report
    """
    report = {
        "analysis_date": datetime.now().isoformat(),
        "root_path": str(root_path),
        "git_status": {},
        "file_statistics": {},
        "directory_structure": {},
        "key_files": [],  # Changed from file_inventory
        "issues": []      # Shortened key name
    }
    
    # Check for Git files and status
    report["git_status"] = check_git_status(root_path)
    
    # Analyze file structure
    report["file_statistics"] = analyze_files(root_path)
    
    # Create directory tree (reduced depth)
    report["directory_structure"] = create_directory_tree(root_path, max_depth=3)
    
    # Create inventory of only key files
    report["key_files"] = create_key_files_inventory(root_path)
    
    # Identify potential issues (shortened)
    report["issues"] = identify_issues(root_path)
    
    return report

def check_git_status(root_path):
    """Check for git files and repository status"""
    git_info = {
        "has_repo": False,
        "git_files": [],
        "gitignore_count": 0,
        "stray_git": []
    }
    
    # Check if it's a git repository
    git_dir = root_path / ".git"
    if git_dir.exists() and git_dir.is_dir():
        git_info["has_repo"] = True
    
    # Look for git-related files
    for root, dirs, files in os.walk(root_path):
        current_path = Path(root)
        relative_path = current_path.relative_to(root_path)
        
        # Check for .git directories
        if ".git" in dirs and str(relative_path) != ".":
            git_info["stray_git"].append(str(relative_path))
        
        # Count .gitignore files
        for file in files:
            if file == ".gitignore":
                git_info["gitignore_count"] += 1
            elif file.startswith(".git") and len(git_info["git_files"]) < 10:
                git_info["git_files"].append(str(relative_path / file))
    
    return git_info

def analyze_files(root_path):
    """Analyze file types and counts"""
    stats = {
        "total_files": 0,
        "total_dirs": 0,
        "file_types": {},
        "frontend": 0,
        "backend": 0,
        "largest_dirs": {}  # Only top 5 directories by file count
    }
    
    dir_file_counts = {}
    
    for root, dirs, files in os.walk(root_path):
        current_path = Path(root)
        relative_path = str(current_path.relative_to(root_path))
        
        stats["total_dirs"] += len(dirs)
        stats["total_files"] += len(files)
        
        # Track directory file counts
        if relative_path not in ["", "."]:
            dir_file_counts[relative_path] = len(files)
        
        # Count files by type (limit to top 10)
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in stats["file_types"]:
                stats["file_types"][ext] += 1
            elif len(stats["file_types"]) < 10:
                stats["file_types"][ext] = 1
            
            # Count frontend vs backend
            if "frontend" in relative_path.lower():
                stats["frontend"] += 1
            elif "backend" in relative_path.lower():
                stats["backend"] += 1
    
    # Only keep top 5 directories by file count
    sorted_dirs = sorted(dir_file_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    stats["largest_dirs"] = dict(sorted_dirs)
    
    return stats

def create_directory_tree(root_path, max_depth=3):
    """Create a simplified directory tree"""
    tree = []
    
    for root, dirs, files in os.walk(root_path):
        current_path = Path(root)
        relative_path = current_path.relative_to(root_path)
        depth = len(relative_path.parts)
        
        if depth >= max_depth:
            continue
            
        if relative_path.parts:
            tree.append({
                "path": str(relative_path),
                "depth": depth,
                "files": len(files),
                "dirs": len(dirs)
            })
    
    return tree[:30]  # Limit to 30 entries

def create_key_files_inventory(root_path):
    """Create inventory of only the most important files"""
    inventory = []
    
    # Priority files to include
    priority_patterns = {
        "models.py", "views.py", "serializers.py", "urls.py",  # Django
        "main.js", "api.js", "admin.js", "auth.js",           # Frontend
        "settings.py", "requirements.txt", "package.json",     # Config
        "README.md", "Dockerfile", ".gitignore"                # Project
    }
    
    # Key extensions (limited set)
    key_extensions = {".py", ".js", ".html"}
    
    for root, dirs, files in os.walk(root_path):
        current_path = Path(root)
        relative_path = current_path.relative_to(root_path)
        
        for file in files:
            # Include if it's a priority file or has key extension
            if file in priority_patterns or Path(file).suffix in key_extensions:
                file_info = {
                    "path": str(relative_path / file),
                    "name": file,
                    "category": categorize_file(str(relative_path), file)
                }
                inventory.append(file_info)
                
                # Limit total inventory size
                if len(inventory) >= 100:
                    return inventory
    
    return inventory

def categorize_file(path, filename):
    """Simplified file categorization"""
    path_lower = path.lower()
    
    if "frontend" in path_lower:
        if "admin" in path_lower:
            return "Frontend-Admin"
        return "Frontend-User"
    elif "backend" in path_lower:
        if "models" in filename:
            return "Backend-Models"
        elif "views" in filename:
            return "Backend-Views"
        elif "serializers" in filename:
            return "Backend-API"
        return "Backend-Other"
    elif filename.endswith((".md", ".txt")):
        return "Docs"
    elif filename.endswith((".json", ".yml", ".yaml")):
        return "Config"
    
    return "Other"

def identify_issues(root_path):
    """Identify potential organizational issues (condensed)"""
    issues = []
    
    # Check for multiple .gitignore files
    gitignore_count = 0
    git_subdirs = []
    env_files = []
    
    for root, dirs, files in os.walk(root_path):
        current_path = Path(root)
        relative_path = current_path.relative_to(root_path)
        
        if ".gitignore" in files:
            gitignore_count += 1
        
        if ".git" in dirs and str(relative_path) != ".":
            git_subdirs.append(str(relative_path))
        
        for file in files:
            if file.startswith(".env"):
                env_files.append(str(relative_path / file))
    
    # Only add issues if found
    if gitignore_count > 1:
        issues.append(f"Multiple .gitignore files: {gitignore_count}")
    
    if git_subdirs:
        issues.append(f"Git dirs in subdirs: {len(git_subdirs)} found")
    
    if env_files:
        issues.append(f"Env files found: {len(env_files)}")
    
    # Check for missing key files
    key_files = ["README.md", "requirements.txt", "package.json"]
    for file in key_files:
        if not (root_path / file).exists():
            issues.append(f"Missing: {file}")
    
    return issues[:10]  # Limit to 10 issues

def save_report(report, output_path):
    """Save the report to a compact JSON file"""
    # Use compact JSON formatting
    with open(output_path, 'w') as f:
        json.dump(report, f, separators=(',', ':'), indent=1)
    
    file_size = os.path.getsize(output_path)
    print(f"Report saved to: {output_path} (Size: {file_size:,} bytes)")

def print_summary(report):
    """Print a summary of the analysis"""
    print("=== Project Analysis Summary ===")
    print(f"Analysis Date: {report['analysis_date']}")
    print(f"Root Path: {report['root_path']}")
    print("\n--- Git Status ---")
    print(f"Has repo: {report['git_status']['has_repo']}")
    print(f"Stray git dirs: {len(report['git_status']['stray_git'])}")
    print(f".gitignore files: {report['git_status']['gitignore_count']}")
    print("\n--- File Statistics ---")
    print(f"Total Files: {report['file_statistics']['total_files']}")
    print(f"Total Directories: {report['file_statistics']['total_dirs']}")
    print(f"Frontend Files: {report['file_statistics']['frontend']}")
    print(f"Backend Files: {report['file_statistics']['backend']}")
    print("\n--- Key File Types ---")
    for ext, count in sorted(report['file_statistics']['file_types'].items(), 
                           key=lambda x: x[1], reverse=True)[:5]:
        print(f"{ext or 'no extension'}: {count}")
    print("\n--- Issues Found ---")
    for issue in report['issues'][:5]:
        print(f"⚠️  {issue}")
    print(f"\nTotal key files tracked: {len(report['key_files'])}")

if __name__ == "__main__":
    # Change this to your project root path
    PROJECT_ROOT = Path(".")  # Current directory
    
    print("Starting compact project analysis...")
    report = analyze_project_structure(PROJECT_ROOT)
    
    # Save detailed report
    output_file = f"project_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_report(report, output_file)
    
    # Print summary
    print_summary(report)
    
    print(f"\nCompact report saved to: {output_file}")
    print("This report is optimized for size while maintaining key information.")