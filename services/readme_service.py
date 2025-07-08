import os
import time
from typing import Dict, List
from models import ProjectMetadata, BannerConfig
from services.github_service import GitHubService
from services.ai_service import AIService
from services.file_service import FileService
from services.banner_service import BannerService


class ReadmeService:
    """Main service for generating README files"""

    def __init__(self):
        self.github_service = GitHubService()
        self.ai_service = AIService()
        self.file_service = FileService()
        self.banner_service = BannerService()  # 🎨 Add banner service

    def generate_readme(self, owner: str, repo: str, banner_config: BannerConfig = None) -> Dict:
        """Generate README for a repository using Gemini 2.5 Flash with professional banner"""
        start_time = time.time()

        try:
            print(f"🚀 Starting README generation for {owner}/{repo} using Gemini 2.5 Flash")

            # Get repository information
            repo_info = self.github_service.get_repo_info(owner, repo)
            default_branch = self.github_service.get_default_branch(owner, repo)

            print(f"📋 Using branch: {default_branch}")

            # Get repository structure and source files
            repo_structure = self.github_service.get_repo_structure(owner, repo, default_branch)
            source_files = self.github_service.fetch_source_files(owner, repo, repo_structure, default_branch)

            if not source_files:
                raise Exception("No source files found to analyze")

            # Extract metadata first (needed for banner generation)
            metadata = self._analyze_project_metadata(source_files, repo_structure)
            
            # 🎨 Generate DUAL professional banners if requested
            header_banner_url = None
            conclusion_banner_url = None
            
            if banner_config and banner_config.include_banner:
                try:
                    print(f"🎨 Generating DUAL banners: Capsule header + Typing conclusion...")
                    
                    # Generate both banners
                    header_banner_url, conclusion_banner_url = self.banner_service.generate_dual_banners(
                        repo_info=repo_info,
                        metadata=metadata,
                        font=banner_config.font,
                        theme=banner_config.theme,
                        style=banner_config.style
                    )
                    
                    print(f"✅ DUAL banners generated!")
                    print(f"🌊 Header: Capsule {banner_config.style} with {banner_config.theme} theme")
                    print(f"⌨️ Conclusion: Typing SVG with JetBrains Mono")
                    
                except Exception as e:
                    print(f"⚠️ Banner generation failed, continuing without banners: {e}")
                    header_banner_url = None
                    conclusion_banner_url = None

            # Generate README content using AI (include both banners in prompt)
            readme_content = self._generate_readme_content(
                repo_info, source_files, metadata, header_banner_url, conclusion_banner_url
            )

            # Clean content
            clean_content = self._clean_readme_content(readme_content)

            # Save to local file
            file_path = self.file_service.save_readme(owner, repo, clean_content)

            processing_time = round(time.time() - start_time, 2)

            result = {
                'readme_content': clean_content,
                'readme_length': len(clean_content),
                'local_file_path': file_path,
                'processing_time': processing_time,
                'files_analyzed': len(source_files),
                'ai_model_used': 'gemini-2.5-flash',
                'branch_used': default_branch,
                'metadata': metadata.__dict__,
                'repo_info': repo_info,
                'header_banner_url': header_banner_url if banner_config and banner_config.include_banner else None,
                'conclusion_banner_url': conclusion_banner_url if banner_config and banner_config.include_banner else None,
                'dual_banners_enabled': banner_config.include_banner if banner_config else False
            }
            
            return result

        except Exception as e:
            print(f"❌ README generation failed: {e}")
            raise

    def _generate_readme_content(self, repo_info: Dict, source_files: Dict, metadata: ProjectMetadata, header_banner_url: str = None, conclusion_banner_url: str = None) -> str:
        """Generate README content using AI with dual banners"""
        if not source_files:
            return self._create_fallback_readme(repo_info['repo'], repo_info['url'], header_banner_url, conclusion_banner_url)

        project_name = repo_info['repo']
        github_url = repo_info['url']

        print(f"📝 Preparing content for README generation...")
        start_time = time.time()
        
        # Prepare file contents for AI analysis (direct approach)
        file_contents = ""
        existing_readme_content = ""

        for file_path, content in source_files.items():
            file_name = os.path.basename(file_path)

            # Handle existing README separately
            if file_name.lower() in ['readme.md', 'readme.txt', 'readme']:
                existing_readme_content = content[:2000]
                continue

            file_contents += f"\n=== FILE: {file_path} ===\n"
            file_contents += content[:2000]  # Reduced per-file limit to save input tokens for better output
            file_contents += "\n"

        # Create AI prompt with file content and dual banners
        ai_prompt = self._create_ai_prompt_optimized(
            project_name, 
            github_url, 
            file_contents, 
            existing_readme_content,
            metadata,
            header_banner_url,  # 🌊 Header banner
            conclusion_banner_url  # ⌨️ Conclusion banner
        )

        preparation_time = round(time.time() - start_time, 2)
        print(f"✅ Content preparation completed in {preparation_time}s")
        print(f"📊 Total prompt size: {len(ai_prompt):,} characters")

        try:
            print(f"🤖 Generating README with single API call...")
            generation_start = time.time()
            
            generated_readme = self.ai_service.generate_readme(ai_prompt)
            
            generation_time = round(time.time() - generation_start, 2)
            print(f"✅ Generated README in {generation_time}s: {len(generated_readme):,} characters")
            return generated_readme

        except Exception as e:
            print(f"❌ AI generation failed: {e}")
            return self._create_fallback_readme(project_name, github_url, header_banner_url, conclusion_banner_url)
    
    def _create_ai_prompt_optimized(self, project_name: str, github_url: str, 
                                  file_contents: str, existing_readme: str, 
                                  metadata: ProjectMetadata, header_banner_url: str = None, 
                                  conclusion_banner_url: str = None) -> str:
        """Create optimized AI prompt with dual banners"""
        
        # 🎨 DUAL Banner section for prompt
        banner_instruction = ""
        if header_banner_url or conclusion_banner_url:
            banner_instruction = f"""
🎨 DUAL PROFESSIONAL BANNERS:

HEADER BANNER (START OF README):
{f"Include this SICK Capsule Render banner at the very top:" if header_banner_url else "No header banner"}
{f"![Header]({header_banner_url})" if header_banner_url else ""}

CONCLUSION BANNER (END OF README):
{f"Include this animated typing conclusion banner at the very end:" if conclusion_banner_url else "No conclusion banner"}
{f"![Conclusion]({conclusion_banner_url})" if conclusion_banner_url else ""}

Banner Features:
- Header: Professional {metadata.primary_language} waving banner with emojis
- Conclusion: Animated typing effect with JetBrains Mono font
- Both optimized for GitHub dark theme
- Language-specific color schemes
"""
        
        return f"""You are a world-class technical documentation specialist, markdown perfectionist, and UI/UX expert who creates README files that are both visually stunning and technically comprehensive. Your documentation is legendary for being accessible to beginners while impressing senior developers.

PROJECT: {project_name}
REPOSITORY: {github_url}
{banner_instruction}

PROJECT FILES FOR ANALYSIS:
{file_contents}

EXISTING README (USE AS REFERENCE AND EXTRACT USEFUL INFO):
{existing_readme[:1000] if existing_readme else "No existing README found"}

🎯 MISSION: Create a FOCUSED, IMPACTFUL README that highlights the ESSENTIAL information developers need - comprehensive but not overwhelming.

📋 CRITICAL ANALYSIS REQUIREMENTS:
1. DEEPLY ANALYZE THE SOURCE CODE FILES - extract key architectural patterns and main features
2. If existing README contains valuable information, incorporate the BEST parts only
3. Identify the CORE project purpose, target audience, and primary use cases
4. Document the TOP 3-5 features that matter most to users
5. Extract ESSENTIAL technologies and dependencies (not every single package)
6. Create CLEAR, ACTIONABLE installation steps (skip obvious details)
7. Document MAIN API endpoints or key functions (not every method)
8. Focus on PRACTICAL usage examples that developers actually need
9. Write with confidence but stay CONCISE and SCANNABLE

🎨 VISUAL EXCELLENCE & SMART PRESENTATION:

**FOCUSED HEADER DESIGN:**
{f"- START with the professional Capsule Render banner provided above" if header_banner_url else "- Create a clean, impactful header"}
- ONE compelling tagline that instantly communicates value
- 4-6 essential badges that tell the core tech story
- Clean visual hierarchy without excessive decoration
{f"- END with the animated typing conclusion banner for perfect closure" if conclusion_banner_url else ""}

**SMART CONTENT STRUCTURE:**
- Every section should serve a clear, essential purpose
- Use progressive disclosure - start with what matters most
- Prioritize ACTIONABLE information over lengthy explanations
- Keep descriptions concise but informative

**ESSENTIAL SECTIONS ONLY:**
- Brief but compelling project overview
- Key features (top 3-5 only)
- Quick start guide (essential steps only)
- Main usage examples
- Contributing guidelines (if no CONTRIBUTING.md)
- Essential links and contact info

**AVOID THESE COMMON BLOAT PATTERNS:**
- Excessive feature lists with minor details
- Overly detailed architecture explanations
- Long technology justifications
- Redundant installation methods
- Too many code examples for the same concept
- Verbose troubleshooting sections for edge cases

🏗️ FOCUSED TECHNICAL CONTENT:

**ESSENTIAL ARCHITECTURE:**
- Identify the main architectural pattern in 1-2 sentences
- Explain WHY this pattern was chosen (benefits only)
- Skip detailed component interactions unless critical

**SMART TECHNOLOGY PRESENTATION:**
- Present the core tech stack as a simple, scannable list
- Explain technology choices ONLY if they're unique or important
- Use clean presentation (avoid overwhelming tables)

**PRACTICAL FEATURE DOCUMENTATION:**
- Present features as clear user benefits
- Use 1-2 realistic examples per major feature
- Focus on the 80% use case, not edge cases
- Show progression from basic to advanced ONLY if necessary

**STREAMLINED DEVELOPER EXPERIENCE:**
- **Prerequisites**: Essential requirements only with versions
- **Quick Start**: Get developers running in under 3 minutes
- **Configuration**: Most important options with brief explanations
- **Testing**: How to verify it works (keep it simple)

**CONCLUSION EXCELLENCE:**
Every README should end with a brief, inspiring conclusion that includes:
- What makes this project valuable (1-2 sentences)
- Clear next steps for users
- Simple contribution guidelines
- Essential contact information

**CRITICAL QUALITY STANDARDS:**
- Only reference files that actually exist in the analyzed source code
- Every code example must be accurate and runnable
- All installation steps must be tested and verified
- Technical explanations must be both accurate and accessible
- Visual elements must enhance, not distract from, the content

🎯 SUCCESS CRITERIA - CREATE A README THAT:
- Makes developers immediately understand the project's value
- Provides essential information without overwhelming detail
- Is scannable and easy to navigate quickly
- Focuses on practical, actionable content
- Balances professionalism with accessibility
- Gets developers up and running fast
- Highlights what matters most, skips what doesn't

IMPORTANT: After generating this focused README, add metadata in this EXACT format:

---METADATA---
PRIMARY_LANGUAGE: [detected primary programming language]
PROJECT_TYPE: [web_app|mobile_app|api|library|cli_tool|desktop_app|data_science|game|other]
TECH_STACK: [comma-separated list of main technologies/frameworks]
FRAMEWORKS: [comma-separated list of frameworks detected]
---END_METADATA---

Generate a README that sets the gold standard for technical documentation - visually stunning, technically comprehensive, and accessible to all! 🚀✨"""
    def _analyze_project_metadata(self, source_files: Dict, repo_structure: List) -> ProjectMetadata:
        """🔍 Analyze project files to extract metadata for banner generation"""
        
        # Detect primary language
        language_counts = {}
        for file_path in source_files.keys():
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.py':
                language_counts['Python'] = language_counts.get('Python', 0) + 1
            elif ext in ['.js', '.jsx']:
                language_counts['JavaScript'] = language_counts.get('JavaScript', 0) + 1
            elif ext in ['.ts', '.tsx']:
                language_counts['TypeScript'] = language_counts.get('TypeScript', 0) + 1
            elif ext == '.java':
                language_counts['Java'] = language_counts.get('Java', 0) + 1
            elif ext == '.go':
                language_counts['Go'] = language_counts.get('Go', 0) + 1
            elif ext in ['.cpp', '.cc', '.cxx']:
                language_counts['C++'] = language_counts.get('C++', 0) + 1
            elif ext == '.rs':
                language_counts['Rust'] = language_counts.get('Rust', 0) + 1
        
        primary_language = max(language_counts, key=language_counts.get) if language_counts else 'Unknown'
        
        # Detect tech stack and frameworks
        tech_stack = []
        frameworks = []
        
        # Check for common files and dependencies
        for file_path, content in source_files.items():
            file_name = os.path.basename(file_path).lower()
            
            # Python ecosystem
            if file_name in ['requirements.txt', 'pyproject.toml', 'setup.py']:
                if 'fastapi' in content.lower():
                    tech_stack.append('FastAPI')
                    frameworks.append('FastAPI')
                if 'django' in content.lower():
                    tech_stack.append('Django')
                    frameworks.append('Django')
                if 'flask' in content.lower():
                    tech_stack.append('Flask')
                    frameworks.append('Flask')
                if 'streamlit' in content.lower():
                    tech_stack.append('Streamlit')
                    frameworks.append('Streamlit')
            
            # JavaScript/Node ecosystem
            elif file_name == 'package.json':
                if 'react' in content.lower():
                    tech_stack.append('React')
                    frameworks.append('React')
                if 'vue' in content.lower():
                    tech_stack.append('Vue.js')
                    frameworks.append('Vue.js')
                if 'angular' in content.lower():
                    tech_stack.append('Angular')
                    frameworks.append('Angular')
                if 'express' in content.lower():
                    tech_stack.append('Express.js')
                    frameworks.append('Express.js')
                if 'next' in content.lower():
                    tech_stack.append('Next.js')
                    frameworks.append('Next.js')
        
        # Add primary language to tech stack if not already there
        if primary_language not in tech_stack:
            tech_stack.insert(0, primary_language)
        
        # Determine project type
        project_type = 'library'  # default
        if any('main.py' in f or 'app.py' in f or 'server.py' in f for f in source_files.keys()):
            if 'FastAPI' in frameworks or 'Flask' in frameworks or 'Django' in frameworks:
                project_type = 'api'
            else:
                project_type = 'cli_tool'
        elif any('index.html' in f or 'app.js' in f for f in source_files.keys()):
            project_type = 'web_app'
        elif 'React' in frameworks or 'Vue.js' in frameworks or 'Angular' in frameworks:
            project_type = 'web_app'
        
        return ProjectMetadata(
            primary_language=primary_language,
            project_type=project_type,
            tech_stack=tech_stack[:5],  # Limit to top 5
            frameworks=frameworks[:3]   # Limit to top 3
        )
    
    def _create_fallback_readme(self, repo_name: str, repo_url: str, header_banner_url: str = None, conclusion_banner_url: str = None) -> str:
        """Create a basic fallback README with dual banners"""
        
        header_section = f"![Header]({header_banner_url})\n\n" if header_banner_url else ""
        conclusion_section = f"\n\n![Conclusion]({conclusion_banner_url})" if conclusion_banner_url else ""
        
        return f"""{header_section}# {repo_name}

A project hosted at {repo_url}

## About

This project is currently being analyzed. Please check back later for a comprehensive README.

## Quick Start

```bash
git clone {repo_url}
cd {repo_name}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

Please check the repository for license information.{conclusion_section}
"""

    def _create_ai_prompt_legacy(self, project_name: str, github_url: str, file_contents: str, existing_readme: str) -> str:
        """Create the AI prompt for README generation"""
        return f"""You are a senior technical documentation specialist, Best UI/UX Designer of the year who's known for paying attention to smallest details, a perfectionist in design and drafting, and software architect creating enterprise-grade README documentation.

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
- **AI Model**: Gemini 2.5 Flash (Optimized with File Summarization)

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
        return ['gemini-2.5-flash']
