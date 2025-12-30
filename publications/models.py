from django.db import models
from users.models import Author, Institution
from django.core.validators import MinValueValidator, MaxValueValidator


class Publication(models.Model):
    """
    Main publication/article model similar to ResearchGate publications.
    Stores comprehensive metadata about research articles.
    """
    PUBLICATION_TYPE_CHOICES = [
        ('journal_article', 'Journal Article'),
        ('conference_paper', 'Conference Paper'),
        ('book_chapter', 'Book Chapter'),
        ('preprint', 'Preprint'),
        ('thesis', 'Thesis/Dissertation'),
        ('technical_report', 'Technical Report'),
        ('poster', 'Poster'),
        ('presentation', 'Presentation'),
        ('book', 'Book'),
        ('review', 'Review Article'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='publications')
    title = models.CharField(max_length=500)
    abstract = models.TextField(blank=True, help_text="Publication abstract")
    publication_type = models.CharField(max_length=30, choices=PUBLICATION_TYPE_CHOICES, default='journal_article')
    
    # File Upload
    pdf_file = models.FileField(upload_to='publications/pdfs/', blank=True, null=True, help_text="Upload PDF of the publication")
    
    # Publication Details
    doi = models.CharField(max_length=255, blank=True, help_text="Digital Object Identifier", db_index=True)
    published_date = models.DateField(blank=True, null=True, help_text="Publication date")
    journal_name = models.CharField(max_length=300, blank=True, help_text="Journal or conference name")
    volume = models.CharField(max_length=50, blank=True)
    issue = models.CharField(max_length=50, blank=True)
    pages = models.CharField(max_length=50, blank=True, help_text="e.g., 123-145")
    publisher = models.CharField(max_length=200, blank=True)
    
    # Co-authors
    co_authors = models.TextField(blank=True, help_text="Comma-separated list of co-authors")
    
    # Erratum
    erratum_from = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='errata',
        help_text="Original publication if this is an erratum"
    )
    
    # External Links
    pubmed_id = models.CharField(max_length=50, blank=True, help_text="PubMed ID")
    arxiv_id = models.CharField(max_length=50, blank=True, help_text="arXiv ID")
    pubmed_central_id = models.CharField(max_length=50, blank=True, help_text="PMC ID")
    
    # Metadata
    is_published = models.BooleanField(default=True, help_text="Whether the publication is publicly visible")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-published_date', '-created_at']
        indexes = [
            models.Index(fields=['author', '-published_date']),
            models.Index(fields=['doi']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.published_date or 'unpublished'})"


class MeSHTerm(models.Model):
    """
    Medical Subject Headings (MeSH) terms for categorizing publications.
    """
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='mesh_terms')
    term = models.CharField(max_length=255, help_text="MeSH term")
    term_type = models.CharField(
        max_length=50, 
        choices=[
            ('major', 'Major Topic'),
            ('minor', 'Minor Topic'),
        ],
        default='minor'
    )
    
    class Meta:
        unique_together = ['publication', 'term']
    
    def __str__(self):
        return f"{self.term} ({self.publication.title[:50]})"


class PublicationStats(models.Model):
    """
    Statistics for publications including citations, reads, downloads, etc.
    """
    publication = models.OneToOneField(Publication, on_delete=models.CASCADE, related_name='stats')
    
    # Metrics
    citations_count = models.PositiveIntegerField(default=0, help_text="Number of citations")
    reads_count = models.PositiveIntegerField(default=0, help_text="Number of reads")
    downloads_count = models.PositiveIntegerField(default=0, help_text="Number of downloads")
    recommendations_count = models.PositiveIntegerField(default=0, help_text="Number of recommendations")
    
    # Altmetric Score
    altmetric_score = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text="Altmetric attention score"
    )
    
    # Impact
    field_citation_ratio = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        help_text="Relative citation ratio"
    )
    
    # Track updates
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Stats for {self.publication.title[:50]}"


class Citation(models.Model):
    """
    Citations of this publication by other works.
    """
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='citations')
    
    # Citation details
    citing_title = models.CharField(max_length=500, help_text="Title of the work citing this publication")
    citing_authors = models.TextField(help_text="Authors of the citing work")
    citing_doi = models.CharField(max_length=255, blank=True, help_text="DOI of citing work")
    citing_year = models.PositiveIntegerField(blank=True, null=True, help_text="Year of citation")
    citing_journal = models.CharField(max_length=300, blank=True, help_text="Journal/source of citing work")
    
    # Metadata
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-citing_year', '-added_at']
    
    def __str__(self):
        return f"Citation: {self.citing_title[:50]}"


class Reference(models.Model):
    """
    References cited by this publication.
    """
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='references')
    
    # Reference details
    reference_text = models.TextField(help_text="Full reference text")
    reference_title = models.CharField(max_length=500, blank=True)
    reference_authors = models.TextField(blank=True)
    reference_doi = models.CharField(max_length=255, blank=True)
    reference_year = models.PositiveIntegerField(blank=True, null=True)
    reference_journal = models.CharField(max_length=300, blank=True)
    
    # Order in reference list
    order = models.PositiveIntegerField(default=0, help_text="Order in reference list")
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"Reference: {self.reference_title[:50] or self.reference_text[:50]}"


class LinkOut(models.Model):
    """
    External links to more resources for the publication.
    """
    LINK_TYPE_CHOICES = [
        ('pubmed', 'PubMed'),
        ('pmc', 'PubMed Central'),
        ('google_scholar', 'Google Scholar'),
        ('doi', 'DOI Link'),
        ('arxiv', 'arXiv'),
        ('researchgate', 'ResearchGate'),
        ('academia', 'Academia.edu'),
        ('publisher', 'Publisher Website'),
        ('preprint', 'Preprint Server'),
        ('dataset', 'Dataset'),
        ('code', 'Source Code'),
        ('other', 'Other'),
    ]
    
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='link_outs')
    link_type = models.CharField(max_length=30, choices=LINK_TYPE_CHOICES)
    url = models.URLField(max_length=500)
    description = models.CharField(max_length=200, blank=True)
    
    class Meta:
        unique_together = ['publication', 'link_type', 'url']
    
    def __str__(self):
        return f"{self.get_link_type_display()}: {self.url}"


class PublicationRead(models.Model):
    """
    Track when users read publications (for read count).
    """
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='read_events')
    reader_email = models.EmailField(blank=True, help_text="Email of reader if logged in")
    reader_ip = models.GenericIPAddressField(blank=True, null=True, help_text="IP address of reader")
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-read_at']
    
    def __str__(self):
        return f"Read: {self.publication.title[:30]} at {self.read_at}"


# ==================== JOURNAL MODELS ====================

class Journal(models.Model):
    """
    Journal model for institutions to manage their academic journals.
    """
    FREQUENCY_CHOICES = [
        ('monthly', 'Monthly'),
        ('bimonthly', 'Bi-monthly'),
        ('quarterly', 'Quarterly'),
        ('biannual', 'Bi-annual'),
        ('annual', 'Annual'),
    ]
    
    # Owner
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='journals')
    
    # Basic Information
    title = models.CharField(max_length=300, help_text="Journal title")
    short_title = models.CharField(max_length=100, blank=True, help_text="Abbreviated title")
    issn = models.CharField(max_length=20, blank=True, help_text="ISSN number", db_index=True)
    e_issn = models.CharField(max_length=20, blank=True, help_text="Electronic ISSN")
    
    # Description
    description = models.TextField(help_text="About the journal")
    scope = models.TextField(blank=True, help_text="Journal scope and aims")
    cover_image = models.ImageField(upload_to='journals/covers/', blank=True, null=True, help_text="Journal cover image")
    
    # Publication Information
    publisher_name = models.CharField(max_length=200, blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='quarterly')
    established_year = models.PositiveIntegerField(blank=True, null=True, help_text="Year established")
    language = models.CharField(max_length=100, default='English', help_text="Primary language")
    
    # Information Sections
    about_journal = models.TextField(blank=True, help_text="Detailed information about the journal")
    ethics_policies = models.TextField(blank=True, help_text="Ethics and editorial policies")
    writing_formatting = models.TextField(blank=True, help_text="Writing and formatting guidelines")
    submitting_manuscript = models.TextField(blank=True, help_text="Manuscript submission guidelines")
    help_support = models.TextField(blank=True, help_text="Help and support information")
    
    # Contact Information
    contact_email = models.EmailField(blank=True, help_text="Journal contact email")
    contact_phone = models.CharField(max_length=20, blank=True, help_text="Contact phone number")
    contact_address = models.TextField(blank=True, help_text="Contact address")
    website = models.URLField(blank=True, help_text="Journal website")
    
    # External Links
    doi_prefix = models.CharField(max_length=50, blank=True, help_text="DOI prefix for articles")
    
    # Settings
    is_active = models.BooleanField(default=True, help_text="Whether journal is actively publishing")
    is_open_access = models.BooleanField(default=False, help_text="Open access journal")
    peer_reviewed = models.BooleanField(default=True, help_text="Peer-reviewed journal")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['institution', '-created_at']),
            models.Index(fields=['issn']),
        ]
    
    def __str__(self):
        return self.title


class EditorialBoardMember(models.Model):
    """
    Editorial board members for a journal.
    """
    ROLE_CHOICES = [
        ('editor_in_chief', 'Editor-in-Chief'),
        ('associate_editor', 'Associate Editor'),
        ('managing_editor', 'Managing Editor'),
        ('section_editor', 'Section Editor'),
        ('editorial_board', 'Editorial Board Member'),
        ('reviewer', 'Reviewer'),
        ('advisory_board', 'Advisory Board Member'),
    ]
    
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='editorial_board')
    
    # Member Information
    name = models.CharField(max_length=200, help_text="Full name")
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    title = models.CharField(max_length=100, blank=True, help_text="Academic title (e.g., Dr., Prof.)")
    affiliation = models.CharField(max_length=300, blank=True, help_text="Institution affiliation")
    email = models.EmailField(blank=True)
    
    # Profile
    bio = models.TextField(blank=True, help_text="Short biography")
    expertise = models.TextField(blank=True, help_text="Areas of expertise")
    photo = models.ImageField(upload_to='journals/editorial_board/', blank=True, null=True)
    
    # Links
    orcid = models.CharField(max_length=50, blank=True, help_text="ORCID ID")
    website = models.URLField(blank=True)
    
    # Order
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'name']
        unique_together = ['journal', 'email']
    
    def __str__(self):
        return f"{self.name} - {self.get_role_display()} ({self.journal.title})"


class JournalStats(models.Model):
    """
    Statistics and metrics for journals.
    """
    journal = models.OneToOneField(Journal, on_delete=models.CASCADE, related_name='stats')
    
    # Impact Metrics
    impact_factor = models.DecimalField(
        max_digits=6, 
        decimal_places=3, 
        default=0.000,
        validators=[MinValueValidator(0)],
        help_text="Journal Impact Factor"
    )
    cite_score = models.DecimalField(
        max_digits=6, 
        decimal_places=3, 
        default=0.000,
        validators=[MinValueValidator(0)],
        help_text="CiteScore metric"
    )
    h_index = models.PositiveIntegerField(default=0, help_text="H-index")
    
    # Submission Metrics
    acceptance_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Acceptance rate percentage"
    )
    average_review_time = models.PositiveIntegerField(
        default=0, 
        help_text="Average review time in days"
    )
    
    # Engagement Metrics
    total_articles = models.PositiveIntegerField(default=0, help_text="Total published articles")
    total_issues = models.PositiveIntegerField(default=0, help_text="Total published issues")
    total_citations = models.PositiveIntegerField(default=0, help_text="Total citations")
    total_reads = models.PositiveIntegerField(default=0, help_text="Total article reads")
    recommendations = models.PositiveIntegerField(default=0, help_text="Number of recommendations")
    
    # Social Metrics
    social_media_score = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0.00,
        help_text="Social media engagement score"
    )
    
    # Update tracking
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Stats for {self.journal.title}"


class Issue(models.Model):
    """
    Journal issues/volumes.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('upcoming', 'Upcoming'),
        ('current', 'Current Issue'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='issues')
    
    # Issue Information
    volume = models.PositiveIntegerField(help_text="Volume number")
    issue_number = models.PositiveIntegerField(help_text="Issue number")
    title = models.CharField(max_length=300, blank=True, help_text="Special issue title (optional)")
    description = models.TextField(blank=True, help_text="Issue description")
    
    # Cover
    cover_image = models.ImageField(upload_to='journals/issues/covers/', blank=True, null=True)
    
    # Dates
    publication_date = models.DateField(help_text="Publication date")
    submission_deadline = models.DateField(blank=True, null=True, help_text="Submission deadline for this issue")
    
    # Content
    doi = models.CharField(max_length=255, blank=True, help_text="DOI for this issue")
    pages_range = models.CharField(max_length=50, blank=True, help_text="e.g., 1-150")
    
    # Editorial
    editorial_note = models.TextField(blank=True, help_text="Editor's note for this issue")
    guest_editors = models.TextField(blank=True, help_text="Guest editors (for special issues)")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_special_issue = models.BooleanField(default=False, help_text="Is this a special issue?")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-volume', '-issue_number']
        unique_together = ['journal', 'volume', 'issue_number']
        indexes = [
            models.Index(fields=['journal', '-publication_date']),
        ]
    
    def __str__(self):
        return f"{self.journal.title} - Vol. {self.volume}, Issue {self.issue_number}"


class IssueArticle(models.Model):
    """
    Link articles to specific journal issues.
    """
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='articles')
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='issue_appearances')
    
    # Article position in issue
    order = models.PositiveIntegerField(default=0, help_text="Article order in issue")
    section = models.CharField(max_length=100, blank=True, help_text="Section (e.g., Research, Review, Editorial)")
    
    # Metadata
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'id']
        unique_together = ['issue', 'publication']
    
    def __str__(self):
        return f"{self.publication.title} in {self.issue}"
