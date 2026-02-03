from django.db import models
from django.core.validators import MinLengthValidator


class SupportPageType(models.TextChoices):
    AUTHOR_SUPPORTER = 'author_supporter', 'Author Supporter Model'
    INSTITUTIONAL_SUPPORTER = 'institutional_supporter', 'Institutional Supporter Model'
    SPONSORSHIP_PARTNERSHIP = 'sponsorship_partnership', 'Sponsorship & Partnership'


class SupportPage(models.Model):
    """Main support page content"""
    page_type = models.CharField(
        max_length=50,
        choices=SupportPageType.choices,
        unique=True,
        help_text="Type of support page"
    )
    title = models.CharField(
        max_length=200,
        help_text="Page title"
    )
    overview = models.TextField(
        help_text="Overview section content (rich text JSON)",
        validators=[MinLengthValidator(10)]
    )
    
    # Sponsorship & Partnership fields (only for sponsorship_partnership page_type)
    sponsorship_detail = models.TextField(
        blank=True,
        help_text="Sponsorship details and benefits (rich text/HTML)"
    )
    partnership_detail = models.TextField(
        blank=True,
        help_text="Partnership details and benefits (rich text/HTML)"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Support Page"
        verbose_name_plural = "Support Pages"
        ordering = ['page_type']

    def __str__(self):
        return f"{self.get_page_type_display()}"


class PricingTier(models.Model):
    """Pricing tiers for support models"""
    support_page = models.ForeignKey(
        SupportPage,
        on_delete=models.CASCADE,
        related_name='pricing_tiers'
    )
    category = models.CharField(
        max_length=200,
        help_text="Pricing category (e.g., 'Senior Researcher / Professor')"
    )
    npr_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount in Nepali Rupees"
    )
    usd_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount in US Dollars"
    )
    purpose = models.TextField(
        help_text="Purpose of this pricing tier"
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order"
    )

    class Meta:
        verbose_name = "Pricing Tier"
        verbose_name_plural = "Pricing Tiers"
        ordering = ['support_page', 'order']

    def __str__(self):
        return f"{self.support_page.get_page_type_display()} - {self.category}"


class SupportBenefit(models.Model):
    """Benefits for supporters"""
    support_page = models.ForeignKey(
        SupportPage,
        on_delete=models.CASCADE,
        related_name='benefits'
    )
    title = models.CharField(
        max_length=200,
        help_text="Benefit title",
        blank=True
    )
    description = models.TextField(
        help_text="Benefit description (rich text JSON or plain text)"
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order"
    )

    class Meta:
        verbose_name = "Support Benefit"
        verbose_name_plural = "Support Benefits"
        ordering = ['support_page', 'order']

    def __str__(self):
        return f"{self.support_page.get_page_type_display()} - {self.title or self.description[:50]}"


class WhySupportPoint(models.Model):
    """Why support NRI points"""
    support_page = models.ForeignKey(
        SupportPage,
        on_delete=models.CASCADE,
        related_name='why_support_points'
    )
    title = models.CharField(
        max_length=200,
        help_text="Point title"
    )
    description = models.TextField(
        help_text="Point description (rich text JSON)"
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order"
    )

    class Meta:
        verbose_name = "Why Support Point"
        verbose_name_plural = "Why Support Points"
        ordering = ['support_page', 'order']

    def __str__(self):
        return f"{self.support_page.get_page_type_display()} - {self.title}"


class Sponsor(models.Model):
    """Sponsors and partners"""
    name = models.CharField(
        max_length=200,
        help_text="Sponsor/Partner name"
    )
    logo = models.ImageField(
        upload_to='sponsors/',
        help_text="Logo image"
    )
    website_url = models.URLField(
        blank=True,
        null=True,
        help_text="Sponsor website URL"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Show on website"
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order"
    )
    
    # Which pages to show on
    show_on_author_supporter = models.BooleanField(
        default=False,
        help_text="Show on Author Supporter page"
    )
    show_on_institutional_supporter = models.BooleanField(
        default=False,
        help_text="Show on Institutional Supporter page"
    )
    show_on_sponsorship_partnership = models.BooleanField(
        default=False,
        help_text="Show on Sponsorship & Partnership page"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sponsor/Partner"
        verbose_name_plural = "Sponsors/Partners"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name




