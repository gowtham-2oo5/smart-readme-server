import json
import urllib.request
import urllib.parse
import base64
import os
from typing import Dict, List, Optional
from config import Config

class GitHubService:
    def __init__(self):
        self.github_token = Config.GITHUB_TOKEN
    
    def get_repo_info(self, owner: str, repo: str) -> Dict[str, str]:
        """Get basic repository information"""
        return {
            'owner': owner,
            'repo': repo,
            'url': f"https://github.com/{owner}/{repo}"
        }
    
    def get_default_branch(self, owner: str, repo: str) -> str:
        """Get the default branch of the repository"""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}"
            req = urllib.request.Request(url)
            
            if self.github_token:
                req.add_header('Authorization', f'token {self.github_token}')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return data.get('default_branch', 'main')
        except Exception as e:
            print(f"❌ Failed to get default branch: {e}")
        
        return 'main'
    
    def get_repo_structure(self, owner: str, repo: str, branch: str) -> List[Dict]:
        """Get repository file structure"""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            req = urllib.request.Request(url)
            
            if self.github_token:
                req.add_header('Authorization', f'token {self.github_token}')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return data.get('tree', [])
        except Exception as e:
            print(f"❌ Failed to get repository structure: {e}")
        
        return []
    
    def fetch_file_content(self, owner: str, repo: str, file_path: str, branch: str) -> Optional[str]:
        """Fetch content of a specific file"""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
            req = urllib.request.Request(url)
            
            if self.github_token:
                req.add_header('Authorization', f'token {self.github_token}')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    if data.get('content') and data.get('size', 0) < 100000:
                        content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
                        return content
        except Exception as e:
            print(f"❌ Failed to fetch {file_path}: {e}")
        
        return None
    
    def fetch_source_files(self, owner: str, repo: str, repo_structure: List[Dict], branch: str) -> Dict[str, str]:
        """Fetch comprehensive source files from repository"""
        print("🔍 Fetching source files...")
        
        source_files = {}
        
        # Priority files (configuration, documentation) - ENHANCED
        priority_files = [
            # General config files
            'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pom.xml',
            'composer.json', 'Gemfile', 'setup.py', 'pyproject.toml', 'Dockerfile',
            'docker-compose.yml', 'README.md', 'README.txt', 'README',
            
            # Android specific files
            'AndroidManifest.xml', 'build.gradle', 'app/build.gradle', 
            'gradle.properties', 'settings.gradle', 'proguard-rules.pro',
            
            # iOS specific files
            'Info.plist', 'Podfile', 'Podfile.lock', 'project.pbxproj',
            'AppDelegate.swift', 'AppDelegate.m', 'SceneDelegate.swift',
            
            # Flutter specific files
            'pubspec.yaml', 'pubspec.lock', 'analysis_options.yaml',
            'lib/main.dart', 'android/app/build.gradle', 'ios/Runner/Info.plist'
        ]
        
        # Critical files that need full content (no truncation)
        critical_files = [
            'build.gradle', 'app/build.gradle', 'package.json', 'pubspec.yaml',
            'AndroidManifest.xml', 'Info.plist', 'Podfile', 'requirements.txt',
            'pom.xml', 'Cargo.toml', 'go.mod'
        ]
        
        # Code file extensions - ENHANCED
        code_extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', 
            '.php', '.rb', '.cpp', '.c', '.h', '.cs', '.swift', '.kt',
            '.dart', '.m', '.mm', '.scala', '.clj', '.ex', '.exs',
            '.html','.css'
        ]
        
        # Skip directories - ENHANCED
        skip_dirs = [
            '.git', 'node_modules', 'vendor', '__pycache__', 
            '.next', 'dist', 'build', '.venv', 'venv', 'Pods',
            '.flutter-plugins', '.dart_tool', 'ios/Pods'
        ]
        
        files_to_fetch = []
        
        # Organize files by priority
        for file_info in repo_structure:
            file_path = file_info.get('path', '')
            file_name = os.path.basename(file_path)
            
            # Skip unwanted directories
            if any(skip_dir in file_path.lower() for skip_dir in skip_dirs):
                continue
            
            # Priority files first
            if file_name in priority_files or file_path in priority_files:
                files_to_fetch.insert(0, file_path)
            # Then code files
            elif any(file_path.endswith(ext) for ext in code_extensions):
                files_to_fetch.append(file_path)
        
        # Limit to 35 files for performance (increased from 30)
        files_to_fetch = files_to_fetch[:35]
        
        # Fetch file contents with smart truncation
        for file_path in files_to_fetch:
            content = self.fetch_file_content(owner, repo, file_path, branch)
            if content:
                # Don't truncate critical configuration files
                if any(critical in file_path for critical in critical_files):
                    source_files[file_path] = content
                    print(f"✅ Fetched (FULL): {file_path} ({len(content)} chars)")
                else:
                    # Truncate other files to 3000 chars
                    source_files[file_path] = content[:3000]
                    print(f"✅ Fetched: {file_path} ({len(content[:3000])} chars)")
        
        print(f"✅ Total files fetched: {len(source_files)}")
        return source_files
