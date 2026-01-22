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
    journal = models.ForeignKey(
        'Journal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_publications',
        help_text="Journal this publication belongs to"
    )
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
        # Topic Classification
    topic_branch = models.ForeignKey(
        'TopicBranch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='publications',
        help_text="Topic branch this publication belongs to"
    )
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


# ==================== TOPIC MODELS ====================

class Topic(models.Model):
    """
    Top-level topic/category for organizing publications.
    """
    name = models.CharField(max_length=200, unique=True, help_text="Topic name (e.g., 'Computer Science')")
    slug = models.SlugField(max_length=200, unique=True, help_text="URL-friendly version of the name")
    description = models.TextField(blank=True, help_text="Description of this topic")
    icon = models.CharField(max_length=100, blank=True, help_text="Icon class or emoji for UI")
    is_active = models.BooleanField(default=True, help_text="Whether this topic is active")
    order = models.IntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'order']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def branches_count(self):
        """Return the number of topic branches under this topic."""
        return self.branches.filter(is_active=True).count()
    
    @property
    def publications_count(self):
        """Return the total number of publications under this topic."""
        return Publication.objects.filter(topic_branch__topic=self, is_published=True).count()


class TopicBranch(models.Model):
    """
    Hierarchical subcategory/branch under a main topic.
    Supports up to 4 levels of nesting (Topic > Branch > Sub-branch > Sub-sub-branch).
    Publications are tagged with topic branches at any level.
    """
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='branches')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent branch for nested hierarchy"
    )
    name = models.CharField(max_length=200, help_text="Branch name (e.g., 'Machine Learning')")
    slug = models.SlugField(max_length=200, help_text="URL-friendly version of the name")
    description = models.TextField(blank=True, help_text="Description of this topic branch")
    level = models.IntegerField(default=1, help_text="Hierarchy level (1-4)", validators=[MinValueValidator(1), MaxValueValidator(4)])
    is_active = models.BooleanField(default=True, help_text="Whether this branch is active")
    order = models.IntegerField(default=0, help_text="Display order within parent")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['topic', 'level', 'order', 'name']
        unique_together = [['topic', 'parent', 'slug']]
        verbose_name_plural = 'Topic Branches'
        indexes = [
            models.Index(fields=['topic', 'parent', 'level']),
            models.Index(fields=['topic', 'is_active', 'order']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return f"{self.topic.name} > {self.name}"
    
    @property
    def full_path(self):
        """Return the full hierarchical path."""
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        path.insert(0, self.topic.name)
        return " > ".join(path)
    
    @property
    def children_count(self):
        """Return the number of child branches."""
        return self.children.filter(is_active=True).count()
    
    @property
    def publications_count(self):
        """Return the number of publications in this branch and all descendants."""
        branch_ids = [self.id]
        # Get all descendant branch IDs
        def get_descendant_ids(branch):
            for child in branch.children.all():
                branch_ids.append(child.id)
                get_descendant_ids(child)
        get_descendant_ids(self)
        return Publication.objects.filter(topic_branch_id__in=branch_ids, is_published=True).count()
    
    def save(self, *args, **kwargs):
        # Auto-calculate level based on parent
        if self.parent:
            self.level = self.parent.level + 1
            if self.level > 4:
                raise ValueError("Maximum hierarchy depth is 4 levels")
            # Ensure same topic as parent
            self.topic = self.parent.topic
        else:
            self.level = 1
        super().save(*args, **kwargs)


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


class JournalQuestionnaire(models.Model):
    """
    Comprehensive questionnaire data for journal evaluation and indexing.
    Collected after journal creation to gather detailed information across 12 sections.
    """
    
    # Link to Journal
    journal = models.OneToOneField(Journal, on_delete=models.CASCADE, related_name='questionnaire')
    
    # ==================== SECTION 1: Journal Identity & Formal Data ====================
    # (Most basic fields already exist in Journal model, but we store them here for completeness)
    journal_title = models.CharField(max_length=300, help_text="Journal title")
    issn = models.CharField(max_length=20, blank=True, help_text="ISSN number")
    e_issn = models.CharField(max_length=20, blank=True, help_text="Electronic ISSN")
    publisher_name = models.CharField(max_length=200, help_text="Publisher name")
    publisher_country = models.CharField(max_length=100, help_text="Publisher country")
    year_first_publication = models.PositiveIntegerField(help_text="Year of first publication")
    
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('bimonthly', 'Bi-monthly'),
        ('quarterly', 'Quarterly'),
        ('biannual', 'Bi-annual'),
        ('annual', 'Annual'),
        ('irregular', 'Irregular'),
    ]
    publication_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, help_text="Publication frequency")
    
    FORMAT_CHOICES = [
        ('online', 'Online only'),
        ('print', 'Print only'),
        ('both', 'Both online and print'),
    ]
    publication_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, help_text="Publication format")
    journal_website_url = models.URLField(max_length=500, help_text="Journal website URL")
    contact_email = models.EmailField(help_text="Contact email")
    
    # ==================== SECTION 2: Scientific Scope & Profile ====================
    main_discipline = models.CharField(max_length=200, help_text="Main scientific discipline")
    secondary_disciplines = models.TextField(blank=True, help_text="Secondary disciplines (comma-separated)")
    aims_and_scope = models.TextField(help_text="Aims and scope of the journal")
    
    # Types of published articles (boolean flags)
    publishes_original_research = models.BooleanField(default=True, help_text="Publishes original research articles")
    publishes_review_articles = models.BooleanField(default=False, help_text="Publishes review articles")
    publishes_case_studies = models.BooleanField(default=False, help_text="Publishes case studies")
    publishes_short_communications = models.BooleanField(default=False, help_text="Publishes short communications")
    publishes_other = models.CharField(max_length=500, blank=True, help_text="Other types of articles (specify)")
    
    # ==================== SECTION 3: Editorial Board ====================
    editor_in_chief_name = models.CharField(max_length=200, help_text="Editor-in-Chief name")
    editor_in_chief_affiliation = models.CharField(max_length=300, help_text="Editor-in-Chief affiliation")
    editor_in_chief_country = models.CharField(max_length=100, help_text="Country of Editor-in-Chief")
    editorial_board_members_count = models.PositiveIntegerField(help_text="Number of editorial board members")
    editorial_board_countries = models.TextField(help_text="Countries represented on editorial board (comma-separated)")
    foreign_board_members_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of foreign editorial board members"
    )
    board_details_published = models.BooleanField(help_text="Are full editorial board details published on the website?")
    
    # ==================== SECTION 4: Peer Review Process ====================
    uses_peer_review = models.BooleanField(help_text="Does the journal use peer review?")
    
    PEER_REVIEW_TYPE_CHOICES = [
        ('single_blind', 'Single-blind'),
        ('double_blind', 'Double-blind'),
        ('open', 'Open peer review'),
        ('post_publication', 'Post-publication review'),
        ('other', 'Other'),
    ]
    peer_review_type = models.CharField(
        max_length=30, 
        choices=PEER_REVIEW_TYPE_CHOICES, 
        blank=True,
        help_text="Type of peer review"
    )
    reviewers_per_manuscript = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text="Number of reviewers per manuscript"
    )
    average_review_time_weeks = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text="Average review time in weeks"
    )
    reviewers_external = models.BooleanField(
        default=True,
        help_text="Are reviewers external to the authors' institutions?"
    )
    peer_review_procedure_published = models.BooleanField(
        help_text="Is the peer-review procedure described on the website?"
    )
    peer_review_procedure_url = models.URLField(max_length=500, blank=True, help_text="URL to peer review procedure")
    
    # ==================== SECTION 5: Ethics & Publication Standards ====================
    follows_publication_ethics = models.BooleanField(help_text="Does the journal follow publication ethics?")
    
    # Ethics guidelines (multiple can be true)
    ethics_based_on_cope = models.BooleanField(default=False, help_text="Based on COPE guidelines")
    ethics_based_on_icmje = models.BooleanField(default=False, help_text="Based on ICMJE guidelines")
    ethics_other_guidelines = models.CharField(max_length=500, blank=True, help_text="Other ethics guidelines (specify)")
    
    uses_plagiarism_detection = models.BooleanField(help_text="Plagiarism detection used?")
    plagiarism_software_name = models.CharField(max_length=200, blank=True, help_text="Name of plagiarism software")
    has_retraction_policy = models.BooleanField(help_text="Retraction policy available?")
    retraction_policy_url = models.URLField(max_length=500, blank=True, help_text="URL to retraction policy")
    has_conflict_of_interest_policy = models.BooleanField(help_text="Conflict of interest policy available?")
    conflict_of_interest_policy_url = models.URLField(max_length=500, blank=True, help_text="URL to COI policy")
    
    # ==================== SECTION 6: Publishing Regularity & Stability ====================
    issues_published_in_year = models.PositiveIntegerField(help_text="Number of issues published in the evaluated year")
    all_issues_published_on_time = models.BooleanField(help_text="Were all declared issues published on time?")
    articles_published_in_year = models.PositiveIntegerField(help_text="Number of articles published in the year")
    submissions_rejected = models.PositiveIntegerField(help_text="Number of rejected submissions")
    average_acceptance_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Average acceptance rate (%)"
    )
    
    # ==================== SECTION 7: Authors & Internationalization ====================
    total_authors_in_year = models.PositiveIntegerField(help_text="Total number of authors published in the year")
    foreign_authors_count = models.PositiveIntegerField(help_text="Number of foreign authors")
    author_countries_count = models.PositiveIntegerField(help_text="Number of countries represented by authors")
    foreign_authors_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of foreign authors"
    )
    encourages_international_submissions = models.BooleanField(help_text="Does the journal encourage international submissions?")
    
    # ==================== SECTION 8: Open Access & Fees ====================
    is_open_access = models.BooleanField(help_text="Is the journal Open Access?")
    
    OA_MODEL_CHOICES = [
        ('gold', 'Gold OA'),
        ('hybrid', 'Hybrid OA'),
        ('diamond', 'Diamond OA (no fees)'),
        ('green', 'Green OA'),
        ('bronze', 'Bronze OA'),
        ('not_oa', 'Not Open Access'),
    ]
    oa_model = models.CharField(
        max_length=20, 
        choices=OA_MODEL_CHOICES,
        blank=True,
        help_text="Open Access model"
    )
    has_apc = models.BooleanField(help_text="Article Processing Charge (APC)?")
    apc_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="APC amount (in USD or local currency)"
    )
    apc_currency = models.CharField(max_length=10, default='USD', help_text="Currency for APC")
    
    LICENSE_CHOICES = [
        ('cc_by', 'CC BY'),
        ('cc_by_sa', 'CC BY-SA'),
        ('cc_by_nc', 'CC BY-NC'),
        ('cc_by_nc_sa', 'CC BY-NC-SA'),
        ('cc_by_nd', 'CC BY-ND'),
        ('cc_by_nc_nd', 'CC BY-NC-ND'),
        ('cc0', 'CC0 (Public Domain)'),
        ('other', 'Other'),
    ]
    license_type = models.CharField(
        max_length=20, 
        choices=LICENSE_CHOICES,
        blank=True,
        help_text="License type"
    )
    
    # ==================== SECTION 9: Digital Publishing Standards ====================
    assigns_dois = models.BooleanField(help_text="Does the journal assign DOIs?")
    doi_registration_agency = models.CharField(max_length=200, blank=True, help_text="DOI registration agency")
    metadata_standards_used = models.TextField(blank=True, help_text="Metadata standards used (comma-separated)")
    uses_online_submission_system = models.BooleanField(help_text="Online submission system used?")
    submission_system_name = models.CharField(max_length=200, blank=True, help_text="Name of submission system")
    
    ARCHIVING_CHOICES = [
        ('lockss', 'LOCKSS'),
        ('clockss', 'CLOCKSS'),
        ('portico', 'Portico'),
        ('institutional', 'Institutional repository'),
        ('pmc', 'PubMed Central'),
        ('other', 'Other'),
        ('none', 'None'),
    ]
    digital_archiving_system = models.CharField(
        max_length=20,
        choices=ARCHIVING_CHOICES,
        blank=True,
        help_text="Digital archiving system"
    )
    other_archiving_system = models.CharField(max_length=200, blank=True, help_text="Other archiving system (specify)")
    
    # ==================== SECTION 10: Indexing & Visibility ====================
    indexed_databases = models.TextField(help_text="Databases where the journal is indexed (comma-separated)")
    year_first_indexed = models.PositiveIntegerField(blank=True, null=True, help_text="Year first indexed")
    
    # Presence in major databases (boolean flags)
    indexed_in_google_scholar = models.BooleanField(default=False, help_text="Indexed in Google Scholar")
    indexed_in_doaj = models.BooleanField(default=False, help_text="Indexed in DOAJ")
    indexed_in_scopus = models.BooleanField(default=False, help_text="Indexed in Scopus")
    indexed_in_web_of_science = models.BooleanField(default=False, help_text="Indexed in Web of Science")
    
    abstracting_services = models.TextField(blank=True, help_text="Abstracting services used (comma-separated)")
    
    # ==================== SECTION 11: Website Quality & Transparency ====================
    author_guidelines_available = models.BooleanField(help_text="Are author guidelines publicly available?")
    peer_review_rules_available = models.BooleanField(help_text="Are peer review rules publicly available?")
    apcs_clearly_stated = models.BooleanField(help_text="Are APCs clearly stated on website?")
    journal_archive_accessible = models.BooleanField(help_text="Is the journal archive publicly accessible?")
    
    # ==================== SECTION 12: Declarations & Verification ====================
    data_is_verifiable = models.BooleanField(help_text="All data provided is true and verifiable")
    data_matches_website = models.BooleanField(help_text="Data corresponds to information on the journal website")
    consent_to_evaluation = models.BooleanField(help_text="Consent to Index Copernicus evaluation or similar indexing")
    completed_by_name = models.CharField(max_length=200, help_text="Name of person completing the survey")
    completed_by_role = models.CharField(max_length=200, help_text="Role of person completing the survey")
    submission_date = models.DateTimeField(auto_now_add=True, help_text="Questionnaire submission date")
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True, help_text="Last update timestamp")
    is_complete = models.BooleanField(default=False, help_text="Is the questionnaire complete?")
    
    class Meta:
        verbose_name = "Journal Questionnaire"
        verbose_name_plural = "Journal Questionnaires"
    
    def __str__(self):
        return f"Questionnaire for {self.journal.title}"
    
    def calculate_completeness(self):
        """Calculate what percentage of the questionnaire is filled."""
        # Count required fields that are filled
        # This is a simplified version - you can make it more sophisticated
        required_fields = [
            self.journal_title, self.publisher_name, self.publisher_country,
            self.year_first_publication, self.main_discipline, self.aims_and_scope,
            self.editor_in_chief_name, self.data_is_verifiable, self.data_matches_website
        ]
        filled = sum(1 for field in required_fields if field)
        return (filled / len(required_fields)) * 100
