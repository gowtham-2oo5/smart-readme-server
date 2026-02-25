import urllib.parse
from typing import Dict, List, Optional, Tuple
from models import ProjectMetadata

class BannerService:
    """🎨 DUAL Professional Banner Service - Capsule Header + Typing Conclusion"""
    
    def __init__(self):
        # ✅ BOTH WORKING APIs
        self.capsule_base = "https://capsule-render.vercel.app/api"
        self.typing_svg_base = "https://readme-typing-svg.demolab.com"
        
        # 🎨 Professional Dark Themes
        self.dark_themes = {
            'midnight': '0:0f0f23,100:1a1a2e',
            'cyberpunk': '0:0f3460,100:16213e', 
            'obsidian': '0:1e1e1e,100:2d2d2d',
            'github_dark': '0:0d1117,100:21262d',
            'matrix': '0:0a0a0a,100:1a1a1a',
            'neon': '0:0f0f23,100:1a1a2e',
            'carbon': '0:161618,100:23252a'
        }
        
        # 🌈 Language-specific color schemes (Capsule format)
        self.language_colors = {
            'Python': '0:3776AB,100:FFD43B',
            'JavaScript': '0:F7DF1E,100:323330',
            'TypeScript': '0:3178C6,100:007ACC',
            'Java': '0:ED8B00,100:FF6B35',
            'Go': '0:00ADD8,100:5DC9E2',
            'Rust': '0:CE422B,100:A72145',
            'C++': '0:00599C,100:659AD2',
            'C#': '0:239120,100:512BD4',
            'PHP': '0:777BB4,100:8892BF',
            'Ruby': '0:CC342D,100:FE1616',
            'Swift': '0:FA7343,100:FF8C00',
            'Kotlin': '0:7F52FF,100:0095D5',
            'default': '0:667eea,100:764ba2'
        }
        
        # Typing SVG colors (single color format)
        self.typing_colors = {
            'Python': '3776AB',
            'JavaScript': 'F7DF1E',
            'TypeScript': '3178C6',
            'Java': 'ED8B00',
            'Go': '00ADD8',
            'Rust': 'CE422B',
            'C++': '00599C',
            'C#': '239120',
            'PHP': '777BB4',
            'Ruby': 'CC342D',
            'Swift': 'FA7343',
            'Kotlin': '7F52FF',
            'default': '667eea'
        }
    
    def generate_dual_banners(
        self, 
        repo_info: Dict, 
        metadata: ProjectMetadata,
        font: str = 'jetbrains',
        theme: str = 'github_dark',
        style: str = 'professional'
    ) -> Tuple[str, str]:
        """🔥 Generate BOTH header and conclusion banners"""
        
        header_banner = self._generate_capsule_header(repo_info, metadata, theme, style)
        conclusion_banner = self._generate_typing_conclusion(repo_info, metadata, theme)
        
        return header_banner, conclusion_banner
    
    def generate_typing_banner(
        self, 
        repo_info: Dict, 
        metadata: ProjectMetadata,
        font: str = 'jetbrains',
        theme: str = 'github_dark',
        style: str = 'professional'
    ) -> str:
        """🎨 Generate header banner (Capsule Render for compatibility)"""
        return self._generate_capsule_header(repo_info, metadata, theme, style)
    
    def _generate_capsule_header(
        self, 
        repo_info: Dict, 
        metadata: ProjectMetadata,
        theme: str,
        style: str
    ) -> str:
        """🌊 SICK Capsule Render Header Banner"""
        
        project_name = repo_info['repo'].replace('-', ' ').replace('_', ' ').title()
        tech_stack = metadata.tech_stack[:3]
        
        description = f"⚡ {metadata.primary_language} {metadata.project_type.title()}"
        if tech_stack:
            description += f" • {' + '.join(tech_stack)}"
        
        color = self.language_colors.get(metadata.primary_language, 'timeAuto')
        
        if style == 'professional':
            banner_type = 'soft'
            height = '150'
        elif style == 'animated':
            banner_type = 'waving'
            height = '150'
        elif style == 'minimal':
            banner_type = 'rect'
            height = '120'
        else:
            banner_type = 'soft'
            height = '150'
        
        params = {
            'type': banner_type,
            'color': color,
            'height': height,
            'section': 'header',
            'text': project_name,
            'fontSize': '50',
            'fontColor': 'ffffff',
            'fontAlign': '50',
            'fontAlignY': '40',
            'desc': description,
            'descSize': '18',
            'descAlign': '50',
            'descAlignY': '65',
            'animation': 'fadeIn'
        }
        
        return f"{self.capsule_base}?{urllib.parse.urlencode(params)}"
    
    def _generate_typing_conclusion(
        self, 
        repo_info: Dict, 
        metadata: ProjectMetadata,
        theme: str
    ) -> str:
        """⌨️ COOL Typing SVG Conclusion Banner"""
        
        project_name = repo_info['repo'].replace('-', ' ').replace('_', ' ').title()
        
        # 🎯 Conclusion messages (NO EMOJIS for typing SVG)
        conclusion_lines = [
            f"Thanks for checking out {project_name}!",
            "Star this repo if you found it helpful",
            "Built with love for the developer community"
        ]
        
        color = self.typing_colors.get(metadata.primary_language, self.typing_colors['default'])
        
        params = {
            'lines': ';'.join(conclusion_lines),
            'font': 'Inter',
            'size': '20',
            'duration': '3500',
            'pause': '1500',
            'color': color,
            'center': 'true',
            'width': '600',
            'height': '60'
        }
        
        return f"{self.typing_svg_base}/?{urllib.parse.urlencode(params)}"
    
    def get_banner_preview_html(self, banner_url: str, banner_name: str) -> str:
        """🖼️ Generate HTML preview for banner"""
        return f"""
        <div style="text-align: center; padding: 20px; background: #0d1117; border-radius: 8px;">
            <h3 style="color: #00ff88; margin-bottom: 15px;">{banner_name}</h3>
            <img src="{banner_url}" alt="{banner_name}" style="max-width: 100%; border-radius: 8px;">
            <div style="margin-top: 10px; padding: 10px; background: #161b22; border-radius: 4px;">
                <code style="color: #7c3aed; font-size: 12px; word-break: break-all;">{banner_url}</code>
            </div>
        </div>
        """
    
    def get_supported_fonts(self) -> Dict[str, str]:
        """📝 Get available fonts"""
        return {
            'jetbrains': 'JetBrains Mono',
            'default': 'Default Font'
        }
    
    def get_supported_themes(self) -> Dict[str, str]:
        """🎨 Get available dark themes"""
        return self.dark_themes
    
    def get_language_colors(self, language: str) -> str:
        """🌈 Get colors for specific language"""
        return self.language_colors.get(language, self.language_colors['default'])
