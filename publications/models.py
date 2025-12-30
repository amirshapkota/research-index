from django.db import models
from users.models import Author
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
