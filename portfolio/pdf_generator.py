from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from io import BytesIO
from django.utils import timezone

class ResumePDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        # Color scheme
        self.primary_color = colors.HexColor('#2E86AB') 
        self.secondary_color = colors.HexColor('#6C757D') 
        self.accent_color = colors.HexColor("#2E86AB") 
        self.dark_color = colors.HexColor('#2B2D42') 
        self.light_bg = colors.HexColor('#F8F9FA')
        
        # Only add style if it doesn't exist
        if 'NameTitle' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='NameTitle',
                parent=self.styles['Heading1'],
                fontSize=26,
                textColor=self.primary_color,
                spaceAfter=8,
                alignment=1,  # Center aligned
                fontName='Helvetica-Bold'
            ))
        
        if 'JobTitle' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='JobTitle',
                parent=self.styles['Heading2'],
                fontSize=16,
                textColor=self.secondary_color,
                spaceAfter=16,
                alignment=1,  # Center aligned
                fontName='Helvetica-Oblique'
            ))
        
        if 'SectionTitle' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='SectionTitle',
                parent=self.styles['Heading2'],
                fontSize=14,
                textColor=self.dark_color,
                spaceAfter=8,
                spaceBefore=16,
                fontName='Helvetica-Bold',
                leftIndent=0,
                borderPadding=5,
                backColor=self.light_bg
            ))
        
        if 'ContactInfo' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='ContactInfo',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=self.secondary_color,
                alignment=1,  # Center aligned
                spaceAfter=8
            ))
        
        if 'SummaryText' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='SummaryText',
                parent=self.styles['Normal'],
                fontSize=11,
                textColor=self.dark_color,
                spaceAfter=12,
                alignment=0,  # Left aligned
                leading=14
            ))
        
        if 'CustomBodyText' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='CustomBodyText',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=self.dark_color,
                spaceAfter=4,
                leftIndent=10,
                leading=12
            ))
        
        if 'LinkStyle' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='LinkStyle',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=self.accent_color,
                spaceAfter=4,
                alignment=1  # Center aligned
            ))
        
        # Professional experience styles
        for s in ['Company', 'Position', 'Date']:
            if s not in self.styles.byName:
                self.styles.add(ParagraphStyle(
                    name=s,
                    parent=self.styles['Normal'],
                    fontSize=12 if s=='Company' else 11,
                    textColor=self.dark_color if s=='Company' else self.primary_color,
                    spaceAfter=2 if s!='Date' else 8,
                    fontName='Helvetica-Bold' if s=='Company' else 'Helvetica'
                ))

    def add_section_header(self, story, title):
        """Add a styled section header with horizontal line"""
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(title, self.styles['SectionTitle']))
        story.append(HRFlowable(
            width="100%",
            thickness=1,
            color=self.primary_color,
            spaceAfter=8,
            spaceBefore=4
        ))

    def generate_resume_pdf(self, resume):
        """Generate PDF for the given resume and return BytesIO buffer"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.6*inch,
            rightMargin=0.6*inch
        )
        story = []

        # Header Section
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(resume.name.upper(), self.styles['NameTitle']))
        
        # Contact info
        contact_parts = []
        if resume.email:
            contact_parts.append(resume.email)
        if resume.phone:
            contact_parts.append(resume.phone)
        if resume.location:
            contact_parts.append(resume.location)
        
        if contact_parts:
            contact_text = " • ".join(contact_parts)
            story.append(Paragraph(contact_text, self.styles['ContactInfo']))

        # Social Links
        social_links = []
        if resume.linkedin_url:
            social_links.append(f"LinkedIn: {resume.linkedin_url}")
        if resume.github_url:
            social_links.append(f"GitHub: {resume.github_url}")
        if resume.portfolio_url:
            social_links.append(f"Portfolio: {resume.portfolio_url}")
        
        if social_links:
            story.append(Paragraph(" | ".join(social_links), self.styles['LinkStyle']))

        story.append(Spacer(1, 0.2*inch))

        # Professional Summary
        if resume.summary and resume.summary.strip():
            self.add_section_header(story, "PROFESSIONAL SUMMARY")
            # Clean up summary text
            summary_text = ' '.join(resume.summary.split())
            story.append(Paragraph(summary_text, self.styles['SummaryText']))

        # Professional Experience
        if hasattr(resume, 'experiences') and resume.experiences.exists():
            self.add_section_header(story, "PROFESSIONAL EXPERIENCE")
            for exp in resume.experiences.all().order_by('-start_date'):
                # Date range formatting
                date_range = f"{exp.start_date.strftime('%b %Y') if exp.start_date else ''} - "
                date_range += "Present" if exp.current else (exp.end_date.strftime('%b %Y') if exp.end_date else "")
                
                # Create a table for better alignment
                exp_data = [
                    [
                        Paragraph(f"<b>{exp.company or ''}</b>", self.styles['Company']),
                        Paragraph(date_range, self.styles['Date'])
                    ],
                    [
                        Paragraph(exp.position or "", self.styles['Position']),
                        Paragraph("", self.styles['Date'])  # Empty cell for alignment
                    ]
                ]
                
                exp_table = Table(exp_data, colWidths=[doc.width * 0.7, doc.width * 0.3])
                exp_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ]))
                story.append(exp_table)
                
                # Experience description with bullet points
                if exp.description:
                    for line in (exp.description or "").split('\n'):
                        if line.strip():
                            story.append(Paragraph(f"• {line.strip()}", self.styles['CustomBodyText']))
                story.append(Spacer(1, 0.1*inch))

        # Skills
        if hasattr(resume, 'skills') and resume.skills.exists():
            self.add_section_header(story, "TECHNICAL SKILLS")

            # Group skills by level
            skills_by_level = {"Beginner": [], "Intermediate": [], "Advanced": [], "Expert": []}
            for skill in resume.skills.all():
                if skill.name:
                    level = skill.level.title() if skill.level else "Other"
                    if level not in skills_by_level:
                        skills_by_level[level] = []
                    skills_by_level[level].append(skill.name)

            # Define the display order
            ordered_levels = ["Expert", "Advanced", "Intermediate", "Beginner"]

            # Display each level in its own section
            for level in ordered_levels:
                skills = skills_by_level.get(level, [])
                if skills:
                    # Add level heading
                    story.append(Paragraph(f'<b><font color="black">{level}:</font></b>', self.styles['Position']))
                    story.append(Paragraph(", ".join(skills), self.styles['CustomBodyText']))
                    story.append(Spacer(1, 0.1 * inch))

        # Projects
        if hasattr(resume, 'resume_projects') and resume.resume_projects.exists():
            self.add_section_header(story, "PROJECTS")
            for proj in resume.resume_projects.all().order_by('-created_at'):
                # Project title
                story.append(Paragraph(f"<b>{proj.name}</b>", self.styles['Company']))
                
                # Project links
                links = []
                if hasattr(proj, 'project_url') and proj.project_url:
                    links.append(f"Live Demo: {proj.project_url}")
                if hasattr(proj, 'github_url') and proj.github_url:
                    links.append(f"Source Code: {proj.github_url}")

                if links:
                    story.append(Paragraph(" | ".join(links), self.styles['LinkStyle']))

                if proj.description:
                    story.append(Paragraph(proj.description, self.styles['CustomBodyText']))

                if hasattr(proj, 'technologies') and proj.technologies:
                    tech_text = f"<b>Technologies:</b> {', '.join(proj.technologies)}"
                    story.append(Paragraph(tech_text, self.styles['CustomBodyText']))

                story.append(Spacer(1, 0.1*inch))

        # Education
        if hasattr(resume, 'educations') and resume.educations.exists():
            self.add_section_header(story, "EDUCATION")
            for edu in resume.educations.all().order_by('-start_date'):
                date_range = f"{edu.start_date.strftime('%b %Y') if edu.start_date else ''} - "
                date_range += "Present" if edu.current else (edu.end_date.strftime('%b %Y') if edu.end_date else "")
                
                edu_data = [
                    [
                        Paragraph(f"<b>{edu.institution or ''}</b>", self.styles['Company']),
                        Paragraph(date_range, self.styles['Date'])
                    ],
                    [
                        Paragraph(edu.degree or "", self.styles['Position']),
                        Paragraph("", self.styles['Date'])
                    ]
                ]
                
                if edu.field_of_study:
                    edu_data.append([
                        Paragraph(f"Field: {edu.field_of_study}", self.styles['CustomBodyText']),
                        Paragraph("", self.styles['Date'])
                    ])
                
                edu_table = Table(edu_data, colWidths=[doc.width * 0.7, doc.width * 0.3])
                edu_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ]))
                story.append(edu_table)
                
                if edu.description:
                    story.append(Paragraph(edu.description, self.styles['CustomBodyText']))
                story.append(Spacer(1, 0.1*inch))

        # Add footer with generation info
        story.append(HRFlowable(
            width="100%",
            thickness=0.5,
            color=self.secondary_color,
            spaceAfter=4,
            spaceBefore=12
        ))
        
        # Use current time for generation timestamp
        current_time = timezone.now()
        footer_text = f"Generated on {current_time.strftime('%B %d, %Y at %I:%M %p')}"
        story.append(Paragraph(footer_text, self.styles['ContactInfo']))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def create_simple_resume_pdf(self, resume_data):
        """Create a simple PDF for testing or basic resumes"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.6*inch,
            rightMargin=0.6*inch
        )
        story = []

        # Basic header
        story.append(Paragraph(resume_data.get('name', '').upper(), self.styles['NameTitle']))
        
        # Basic contact info
        contact_info = []
        if resume_data.get('email'):
            contact_info.append(resume_data['email'])
        if resume_data.get('phone'):
            contact_info.append(resume_data['phone'])
        
        if contact_info:
            story.append(Paragraph(" • ".join(contact_info), self.styles['ContactInfo']))

        # Basic summary
        if resume_data.get('summary'):
            self.add_section_header(story, "SUMMARY")
            story.append(Paragraph(resume_data['summary'], self.styles['SummaryText']))

        doc.build(story)
        buffer.seek(0)
        return buffer