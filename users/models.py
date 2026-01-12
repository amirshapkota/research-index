from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator
from rest_framework_simplejwt.tokens import RefreshToken


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = [
        ('author', 'Author'),
        ('institution', 'Institution'),
        ('admin', 'Admin'),
    ]
    
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_type']
    
    def __str__(self):
        return self.email
    
    def tokens(self):
        """
        Generate JWT tokens with custom claims including user_type.
        """
        refresh = RefreshToken.for_user(self)
        refresh['user_type'] = self.user_type
        refresh['email'] = self.email
        
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class Author(models.Model):
    TITLE_CHOICES = [
        ('Dr.', 'Dr.'),
        ('Prof.', 'Prof.'),
        ('Mr.', 'Mr.'),
        ('Ms.', 'Ms.'),
        ('Mrs.', 'Mrs.'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='author_profile')
    title = models.CharField(max_length=10, choices=TITLE_CHOICES)
    full_name = models.CharField(max_length=200)
    institute = models.CharField(max_length=200)
    designation = models.CharField(max_length=100)
    
    degree = models.CharField(max_length=200, blank=True, help_text="Highest degree (e.g., PhD in Computer Science)")
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/authors/', blank=True, null=True)
    cv = models.FileField(upload_to='cvs/', blank=True, null=True, help_text="Upload CV (PDF recommended)")
    
    # Research profile fields
    bio = models.TextField(blank=True, help_text="Short biography")
    research_interests = models.TextField(blank=True, help_text="Research areas and interests")
    orcid = models.CharField(max_length=50, blank=True, help_text="ORCID ID")
    google_scholar = models.URLField(blank=True, help_text="Google Scholar profile URL")
    researchgate = models.URLField(blank=True, help_text="ResearchGate profile URL")
    linkedin = models.URLField(blank=True, help_text="LinkedIn profile URL")
    website = models.URLField(blank=True, help_text="Personal/academic website")
    
    def __str__(self):
        return f"{self.title} {self.full_name}"
    
    def get_coauthors(self):
        """
        Return a list of unique co-authors (other authors) who have collaborated
        with this author on publications.
        """
        from publications.models import Publication
        
        # Get all publications by this author
        my_publications = Publication.objects.filter(author=self, is_published=True)
        
        # Extract co-authors from the co_authors field
        coauthor_names = set()
        for pub in my_publications:
            if pub.co_authors:
                # Split by comma and clean up
                names = [name.strip() for name in pub.co_authors.split(',') if name.strip()]
                coauthor_names.update(names)
        
        # Try to match with existing Author records
        coauthors_data = []
        for name in coauthor_names:
            # Try to find matching author
            matching_authors = Author.objects.filter(full_name__icontains=name).exclude(id=self.id)
            if matching_authors.exists():
                author = matching_authors.first()
                coauthors_data.append({
                    'id': author.id,
                    'name': author.full_name,
                    'email': author.user.email,
                    'institute': author.institute,
                    'is_registered': True
                })
            else:
                # Non-registered co-author
                coauthors_data.append({
                    'id': None,
                    'name': name,
                    'email': None,
                    'institute': None,
                    'is_registered': False
                })
        
        return coauthors_data
    
    def get_collaboration_count(self):
        """Return the number of unique co-authors."""
        return len(self.get_coauthors())


class AuthorStats(models.Model):
    """
    Statistics for author's research impact and activity.
    Similar to Google Scholar metrics.
    """
    author = models.OneToOneField(Author, on_delete=models.CASCADE, related_name='stats')
    
    # Impact metrics
    h_index = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="h-index: h papers with at least h citations each"
    )
    i10_index = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="i10-index: number of publications with at least 10 citations"
    )
    total_citations = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total number of citations across all publications"
    )
    
    # Engagement metrics
    total_reads = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total number of times publications were read"
    )
    total_downloads = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total number of PDF downloads"
    )
    recommendations_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total recommendations received"
    )
    
    # Additional metrics
    total_publications = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total number of published works"
    )
    average_citations_per_paper = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Average citations per publication"
    )
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Author Statistics'
        verbose_name_plural = 'Author Statistics'
    
    def __str__(self):
        return f"Stats for {self.author.full_name}"
    
    def calculate_h_index(self):
        """
        Calculate h-index: An author has h-index h if h of their publications
        have at least h citations each.
        """
        from publications.models import Publication
        
        # Get all publications with their citation counts
        publications = Publication.objects.filter(
            author=self.author,
            is_published=True
        ).select_related('stats')
        
        citation_counts = []
        for pub in publications:
            if hasattr(pub, 'stats'):
                citation_counts.append(pub.stats.citations_count)
            else:
                citation_counts.append(0)
        
        # Sort in descending order
        citation_counts.sort(reverse=True)
        
        # Calculate h-index
        h = 0
        for i, citations in enumerate(citation_counts, start=1):
            if citations >= i:
                h = i
            else:
                break
        
        return h
    
    def calculate_i10_index(self):
        """
        Calculate i10-index: Number of publications with at least 10 citations.
        """
        from publications.models import Publication
        
        publications = Publication.objects.filter(
            author=self.author,
            is_published=True
        ).select_related('stats')
        
        i10 = 0
        for pub in publications:
            if hasattr(pub, 'stats') and pub.stats.citations_count >= 10:
                i10 += 1
        
        return i10
    
    def update_stats(self):
        """
        Recalculate all statistics from publications.
        """
        from publications.models import Publication
        
        publications = Publication.objects.filter(
            author=self.author,
            is_published=True
        ).select_related('stats')
        
        total_citations = 0
        total_reads = 0
        total_downloads = 0
        total_recommendations = 0
        total_pubs = publications.count()
        
        for pub in publications:
            if hasattr(pub, 'stats'):
                stats = pub.stats
                total_citations += stats.citations_count
                total_reads += stats.reads_count
                total_downloads += stats.downloads_count
                total_recommendations += stats.recommendations_count
        
        # Update fields
        self.total_publications = total_pubs
        self.total_citations = total_citations
        self.total_reads = total_reads
        self.total_downloads = total_downloads
        self.recommendations_count = total_recommendations
        self.h_index = self.calculate_h_index()
        self.i10_index = self.calculate_i10_index()
        
        # Calculate average citations
        if total_pubs > 0:
            self.average_citations_per_paper = round(total_citations / total_pubs, 2)
        else:
            self.average_citations_per_paper = 0.00
        
        self.save()


class Institution(models.Model):
    INSTITUTION_TYPE_CHOICES = [
        ('university', 'University'),
        ('research_institute', 'Research Institute'),
        ('government', 'Government Organization'),
        ('private', 'Private Research Organization'),
        ('industry', 'Industry/Corporate R&D'),
        ('hospital', 'Hospital/Medical Center'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='institution_profile')
    institution_name = models.CharField(max_length=200)
    
    # New fields
    institution_type = models.CharField(max_length=30, choices=INSTITUTION_TYPE_CHOICES, blank=True)
    logo = models.ImageField(upload_to='profiles/institutions/', blank=True, null=True)
    description = models.TextField(blank=True, help_text="About the institution")
    
    # Contact & Location
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Online presence
    website = models.URLField(blank=True)
    established_year = models.PositiveIntegerField(blank=True, null=True, help_text="Year established")
    
    # Research info
    research_areas = models.TextField(blank=True, help_text="Main research areas")
    total_researchers = models.PositiveIntegerField(blank=True, null=True, help_text="Number of researchers")
    
    def __str__(self):
        return self.institution_name


class InstitutionStats(models.Model):
    """
    Statistics for institution's research output and impact.
    Aggregates metrics from all publications associated with the institution.
    """
    institution = models.OneToOneField(Institution, on_delete=models.CASCADE, related_name='stats')
    
    # Publication metrics
    total_publications = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total number of published works from this institution"
    )
    
    # Impact metrics
    total_citations = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total citations across all publications"
    )
    average_citations_per_paper = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Average citations per publication"
    )
    
    # Engagement metrics
    total_reads = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total number of times publications were read"
    )
    total_downloads = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total number of PDF downloads"
    )
    recommendations_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total recommendations received"
    )
    
    # Author metrics
    total_authors = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total number of unique authors from this institution"
    )
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Institution Statistics'
        verbose_name_plural = 'Institution Statistics'
    
    def __str__(self):
        return f"Stats for {self.institution.institution_name}"
    
    def update_stats(self):
        """
        Recalculate all statistics from publications associated with this institution.
        """
        from publications.models import Publication
        
        # Get all publications where the author's institute matches this institution
        publications = Publication.objects.filter(
            author__institute__icontains=self.institution.institution_name,
            is_published=True
        ).select_related('stats').distinct()
        
        total_citations = 0
        total_reads = 0
        total_downloads = 0
        total_recommendations = 0
        total_pubs = publications.count()
        
        for pub in publications:
            if hasattr(pub, 'stats'):
                stats = pub.stats
                total_citations += stats.citations_count
                total_reads += stats.reads_count
                total_downloads += stats.downloads_count
                total_recommendations += stats.recommendations_count
        
        # Count unique authors from this institution
        unique_authors = publications.values('author').distinct().count()
        
        # Update fields
        self.total_publications = total_pubs
        self.total_citations = total_citations
        self.total_reads = total_reads
        self.total_downloads = total_downloads
        self.recommendations_count = total_recommendations
        self.total_authors = unique_authors
        
        # Calculate average citations
        if total_pubs > 0:
            self.average_citations_per_paper = round(total_citations / total_pubs, 2)
        else:
            self.average_citations_per_paper = 0.00
        
        self.save()


