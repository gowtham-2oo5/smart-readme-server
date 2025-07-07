import os
import time
from typing import Dict, Tuple
from models import ProjectMetadata
from services.github_service import GitHubService
from services.ai_service import AIService
from services.file_service import FileService

class ReadmeService:
    """Main service for generating README files"""
    
    def __init__(self):
        self.github_service = GitHubService()
        self.ai_service = AIService()
        self.file_service = FileService()
    
    def generate_readme(self, owner: str, repo: str, ai_model: str) -> Dict:
        """Generate README for a repository using specified AI model"""
        start_time = time.time()
        
        try:
            print(f"🚀 Starting README generation for {owner}/{repo} using {ai_model}")
            
            # Get repository information
            repo_info = self.github_service.get_repo_info(owner, repo)
            default_branch = self.github_service.get_default_branch(owner, repo)
            
            print(f"📋 Using branch: {default_branch}")
            
            # Get repository structure and source files
            repo_structure = self.github_service.get_repo_structure(owner, repo, default_branch)
            source_files = self.github_service.fetch_source_files(owner, repo, repo_structure, default_branch)
            
            if not source_files:
                raise Exception("No source files found to analyze")
            
            # Generate README content using AI
            readme_content = self._generate_readme_content(repo_info, source_files, ai_model)
            
            # Extract metadata and clean content
            metadata = self._extract_metadata(readme_content)
            clean_content = self._clean_readme_content(readme_content)
            
            # Save to local file
            file_path = self.file_service.save_readme(owner, repo, clean_content)
            
            processing_time = round(time.time() - start_time, 2)
            
            return {
                'readme_content': clean_content,
                'readme_length': len(clean_content),
                'local_file_path': file_path,
                'processing_time': processing_time,
                'files_analyzed': len(source_files),
                'ai_model_used': ai_model,
                'branch_used': default_branch,
                'metadata': metadata.__dict__,
                'repo_info': repo_info
            }
            
        except Exception as e:
            print(f"❌ README generation failed: {e}")
            raise
    
    def _generate_readme_content(self, repo_info: Dict, source_files: Dict, ai_model: str) -> str:
        """Generate README content using AI"""
        if not source_files:
            return self._create_fallback_readme(repo_info['repo'], repo_info['url'])
        
        project_name = repo_info['repo']
        github_url = repo_info['url']
        
        # Prepare file contents for AI analysis
        file_contents = ""
        existing_readme_content = ""
        
        for file_path, content in source_files.items():
            file_name = os.path.basename(file_path)
            
            # Handle existing README separately
            if file_name.lower() in ['readme.md', 'readme.txt', 'readme']:
                existing_readme_content = content[:2000]
                continue
            
            file_contents += f"\n=== FILE: {file_path} ===\n"
            file_contents += content[:3000]  # Limit content per file
            file_contents += "\n"
        
        # Create AI prompt
        ai_prompt = self._create_ai_prompt(project_name, github_url, file_contents, existing_readme_content)
        
        try:
            print(f"🤖 Generating README using {ai_model} ({len(ai_prompt)} chars)")
            
            # Generate using specified AI model
            generated_readme = self.ai_service.generate_readme(ai_model, ai_prompt)
            
            print(f"✅ Generated README using {ai_model}: {len(generated_readme)} characters")
            return generated_readme
            
        except Exception as e:
            print(f"❌ AI generation failed with {ai_model}: {e}")
            return self._create_fallback_readme(project_name, github_url)
    
    def _create_ai_prompt(self, project_name: str, github_url: str, file_contents: str, existing_readme: str) -> str:
        """Create the AI prompt for README generation"""
        return f"""You are a senior technical documentation specialist and software architect creating enterprise-grade README documentation.

PROJECT: {project_name}
REPOSITORY: {github_url}

SOURCE CODE AND PROJECT FILES FOR ANALYSIS:
{file_contents}

EXISTING README (USE AS REFERENCE AND EXTRACT USEFUL INFO):
{existing_readme[:500] if existing_readme else "No existing README found"}

🎯 MISSION: Create a COMPREHENSIVE, PROFESSIONAL README that demonstrates deep technical understanding and enterprise-level documentation standards.

📋 CRITICAL ANALYSIS REQUIREMENTS:
1. DEEPLY ANALYZE THE SOURCE CODE FILES - extract architectural patterns, design decisions
2. If existing README contains valuable information (setup steps, configuration details, project description), incorporate and enhance it
3. Identify the ACTUAL project purpose, target audience, and use cases from code structure AND existing documentation
4. Document REAL features with technical depth - combine code analysis with existing documentation insights
3. Document REAL features with technical depth - not just surface-level descriptions
4. Extract ACTUAL technologies, versions, and dependencies from package/build files
5. Create ACCURATE, step-by-step installation with prerequisites and troubleshooting
6. Document REAL API endpoints, functions, classes, and capabilities found in source
7. Identify architectural patterns (MVVM, MVP, Clean Architecture, etc.) from code structure
8. Extract SDK versions, minimum requirements, and platform specifics from build files
9. Write as the project owner - use confident, narrative voice
10. Distinguish frameworks correctly (NextJS vs React, Jetpack Compose vs Views, Flutter vs Native, etc.)
11. Identify UI libraries (shadcn/ui, Material Design, Cupertino, etc.) from dependencies

🏗️ TECHNICAL DEPTH REQUIREMENTS:

**ARCHITECTURE ANALYSIS:**
- Identify and document the architectural pattern used (MVVM, Clean Architecture, BLoC, Provider, etc.)
- Extract project structure and explain key directories/modules
- Document data flow and state management patterns
- Identify dependency injection, navigation patterns, routing

**TECHNOLOGY STACK ANALYSIS:**
- Extract MAIN technologies only (React, Flutter, Spring Boot, etc.) - NOT every dependency
- Focus on PRIMARY frameworks and platforms, not utility libraries
- Distinguish between core tech stack vs development dependencies
- For mobile: Focus on platform (Android/iOS), main framework (Flutter/Native), key libraries only

**FEATURE DOCUMENTATION:**
- Document features based on actual UI screens/components found
- Explain authentication flows, data persistence, networking
- Document any background services, notifications, or integrations
- Include configuration options and customization capabilities
- For mobile apps: Document platform-specific features, permissions

🎨 PROFESSIONAL PRESENTATION REQUIREMENTS:

**VISUAL IMPACT & POLISH:**
- Create a stunning header with perfect badge alignment and visual hierarchy
- Use strategic spacing, dividers, and HTML elements for maximum visual appeal
- Include eye-catching emojis that enhance readability without being overwhelming
- Create a cohesive color scheme through badge selection and formatting
- Make every section visually distinct and scannable

**TECH STACK PRESENTATION:**
- Show ONLY main technologies (React, Flutter, Node.js, MongoDB, etc.)
- Avoid listing utility dependencies, dev tools, or minor libraries
- Focus on what matters to developers evaluating the project
- Use beautiful, consistent badge styling for main tech stack

**CONTENT STRUCTURE:**
- Every section should feel purposeful and well-crafted
- Include smooth transitions between sections
- End with a compelling conclusion that ties everything together
- Make the README feel like a complete, polished document

**VISUAL HIERARCHY:**
- Use HTML elements strategically: <div align="center">, <details>, <summary>, <kbd>
- Create comprehensive badge collection with shields.io (technology, license, platform support)
- Strategic emoji usage for navigation and visual appeal
- Professional typography with proper heading hierarchy

**DEVELOPER EXPERIENCE:**
- **Prerequisites section** with exact requirements (Android Studio, Xcode, Flutter SDK versions, etc.)
- **Step-by-step setup** with actual commands and file paths
- **Configuration examples** with code snippets and file locations
- **Project structure diagram** showing key directories and their purposes
- **Testing instructions** and development workflow
- **Troubleshooting section** with common issues and solutions

**PLATFORM-SPECIFIC SECTIONS:**

**For Android Projects:**
- System requirements (API levels, RAM, storage)
- Build variants and flavors
- Signing configuration
- ProGuard/R8 configuration
- Testing strategy (Unit, UI, Integration)
- Performance considerations

**For iOS Projects:**
- iOS deployment target and device compatibility
- Xcode version requirements
- Provisioning profiles and certificates
- App Store submission guidelines
- TestFlight distribution

**For Flutter Projects:**
- Flutter SDK version compatibility
- Platform-specific setup (Android Studio, Xcode)
- State management approach (BLoC, Provider, Riverpod, etc.)
- Platform channels and native integrations
- Build configurations for both platforms

**For Web Projects:**
- Browser compatibility
- Environment variables and configuration
- Deployment strategies
- Performance metrics
- SEO considerations

**INTERACTIVE ELEMENTS:**
- Collapsible Table of Contents with anchor links
- Expandable sections for advanced configurations
- Code blocks with syntax highlighting and copy indicators
- HTML tables for compatibility matrices and feature comparisons

**PROFESSIONAL FORMATTING EXAMPLES:**
```html
<div align="center">
  <h1>🚀 {project_name}</h1>
  <p><em>Compelling tagline that hooks developers instantly</em></p>
  
  <!-- MAIN TECH STACK ONLY - Beautiful, consistent badges -->
  <img src="https://img.shields.io/badge/Flutter-02569B?style=for-the-badge&logo=flutter&logoColor=white" alt="Flutter">
  <img src="https://img.shields.io/badge/Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black" alt="Firebase">
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License">
  
  <br><br>
  
  <!-- Quick action buttons -->
  <a href="#installation">🚀 Get Started</a> •
  <a href="#features">✨ Features</a> •
  <a href="#demo">📱 Demo</a>
</div>

<hr>
```

**SMART LINKING REQUIREMENTS:**
- ONLY link to files that actually exist in the repository
- Check the source code analysis for existing files before creating links
- If CONTRIBUTING.md doesn't exist, provide inline contribution guidelines
- If LICENSE file doesn't exist, mention license type without linking
- Don't reference non-existent documentation files
- Create self-contained README that doesn't depend on missing files

**CONCLUSION SECTION REQUIREMENT:**
Every README MUST end with a compelling conclusion that includes:
- Summary of what makes this project special
- Call-to-action for contributors or users (inline guidelines if no CONTRIBUTING.md)
- Professional sign-off with available contact information only
- Thank you note to the community
- Future vision or roadmap teaser

Example conclusion format (adapt based on what files actually exist):
```markdown
---

## 🎉 Conclusion

[Project Name] represents [key value proposition]. Built with [main technologies], it offers [primary benefits] for [target audience].

### 🌟 What's Next?
- [ ] Upcoming feature roadmap items
- [ ] Community contributions welcome
- [ ] Feedback and suggestions appreciated

### 🤝 Contributing
We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### 📞 Support & Contact
- 🐛 Issues: Report bugs via GitHub Issues
- 💬 Questions: Open a discussion or issue

---

<div align="center">
  <strong>⭐ Star this repo if you find it helpful!</strong>
  <br>
  <em>Made with ❤️ for the developer community</em>
</div>
```

**CRITICAL RULE: Only reference files that exist in the analyzed source code!**

**QUALITY INDICATORS:**
- Include testing section (shows project maturity)
- Document contribution guidelines
- Explain project structure and architecture
- Provide troubleshooting and FAQ sections
- Include performance considerations and best practices

🎯 SUCCESS CRITERIA:
Create a README that makes senior developers think:
- "This is a well-architected, professional project"
- "The documentation shows deep technical understanding"
- "I can quickly assess if this fits my needs"
- "The setup instructions will actually work"
- "This team knows what they're doing"

IMPORTANT: After generating the README, add a metadata section at the very end in this EXACT format:

---METADATA---
PRIMARY_LANGUAGE: [detected primary programming language like Python, JavaScript, TypeScript, Java, Go, Kotlin, Dart, Swift, etc.]
PROJECT_TYPE: [web_app|mobile_app|api|library|cli_tool|desktop_app|data_science|game|other]
TECH_STACK: [comma-separated list of main technologies/frameworks like React, Node.js, Express, MongoDB, Flutter, Android, iOS, etc.]
FRAMEWORKS: [comma-separated list of frameworks detected like Next.js, Django, Flask, Spring Boot, Flutter, React Native, etc.]
---END_METADATA---

Generate a README that demonstrates MASTERY of both the technology and documentation craft! 🚀"""
    
    def _extract_metadata(self, readme_content: str) -> ProjectMetadata:
        """Extract metadata from README content"""
        try:
            if '---METADATA---' in readme_content and '---END_METADATA---' in readme_content:
                metadata_start = readme_content.find('---METADATA---') + len('---METADATA---')
                metadata_end = readme_content.find('---END_METADATA---')
                metadata_section = readme_content[metadata_start:metadata_end].strip()
                
                metadata_dict = {
                    'primary_language': 'Unknown',
                    'project_type': 'other',
                    'tech_stack': [],
                    'frameworks': []
                }
                
                for line in metadata_section.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'PRIMARY_LANGUAGE':
                            metadata_dict['primary_language'] = value
                        elif key == 'PROJECT_TYPE':
                            metadata_dict['project_type'] = value
                        elif key == 'TECH_STACK':
                            metadata_dict['tech_stack'] = [tech.strip() for tech in value.split(',') if tech.strip()]
                        elif key == 'FRAMEWORKS':
                            metadata_dict['frameworks'] = [fw.strip() for fw in value.split(',') if fw.strip()]
                
                return ProjectMetadata(**metadata_dict)
            
            # Fallback to defaults
            return ProjectMetadata(
                primary_language='Unknown',
                project_type='other',
                tech_stack=[],
                frameworks=[]
            )
            
        except Exception as e:
            print(f"❌ Error extracting metadata: {e}")
            return ProjectMetadata(
                primary_language='Unknown',
                project_type='other',
                tech_stack=[],
                frameworks=[]
            )
    
    def _clean_readme_content(self, readme_content: str) -> str:
        """Remove metadata section from README content"""
        if '---METADATA---' in readme_content:
            return readme_content[:readme_content.find('---METADATA---')].strip()
        return readme_content
    
    def _create_fallback_readme(self, project_name: str, github_url: str) -> str:
        """Create fallback README when AI generation fails"""
        return f"""# {project_name}

A project hosted at {github_url}

## About
This project requires further analysis to generate comprehensive documentation.

## Repository
- **Source**: {github_url}
- **Analysis**: Basic fallback documentation

## Next Steps
Please ensure the repository contains analyzable source code files for better documentation generation.

---METADATA---
PRIMARY_LANGUAGE: Unknown
PROJECT_TYPE: other
TECH_STACK: 
FRAMEWORKS: 
---END_METADATA---
"""
    
    def get_supported_models(self) -> list:
        """Get list of supported AI models"""
        return self.ai_service.get_supported_models()
