"""
Management command to create initial support pages with sample data.
"""
from django.core.management.base import BaseCommand
from support.models import (
    SupportPage, PricingTier, SupportBenefit, WhySupportPoint
)


class Command(BaseCommand):
    help = 'Create initial support pages with sample data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\nCreating initial support pages...\n'))

        # Create Author Supporter Page
        author_page, created = SupportPage.objects.get_or_create(
            page_type='author_supporter',
            defaults={
                'title': 'Author Supporter Model',
                'overview': '''Support NRI's mission to advance research excellence in Nepal. 
                Your contribution helps maintain our platform, expand features, and provide 
                free access to researchers across Nepal.''',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created Author Supporter page'))
            
            # Add pricing tiers
            PricingTier.objects.create(
                support_page=author_page,
                category='PhD Student / Junior Researcher',
                npr_amount=500.00,
                usd_amount=5.00,
                purpose='Support platform maintenance and basic features',
                order=1
            )
            PricingTier.objects.create(
                support_page=author_page,
                category='Senior Researcher / Professor',
                npr_amount=1000.00,
                usd_amount=10.00,
                purpose='Support advanced features and journal indexing',
                order=2
            )
            
            # Add benefits
            SupportBenefit.objects.create(
                support_page=author_page,
                title='Priority Support',
                description='Get priority email support for platform issues',
                order=1
            )
            SupportBenefit.objects.create(
                support_page=author_page,
                title='Early Access',
                description='Access new features before public release',
                order=2
            )
            SupportBenefit.objects.create(
                support_page=author_page,
                title='Supporter Badge',
                description='Display a supporter badge on your profile',
                order=3
            )
            
            # Add why support points
            WhySupportPoint.objects.create(
                support_page=author_page,
                title='Maintain Free Access',
                description='Keep the platform free and accessible to all Nepali researchers',
                order=1
            )
            WhySupportPoint.objects.create(
                support_page=author_page,
                title='Improve Infrastructure',
                description='Invest in better servers, faster search, and enhanced features',
                order=2
            )
            WhySupportPoint.objects.create(
                support_page=author_page,
                title='Support Local Research',
                description='Help build a stronger research community in Nepal',
                order=3
            )
            
            self.stdout.write('  Added pricing tiers, benefits, and why support points')
        else:
            self.stdout.write(self.style.WARNING('⚠ Author Supporter page already exists'))

        # Create Institutional Supporter Page
        institutional_page, created = SupportPage.objects.get_or_create(
            page_type='institutional_supporter',
            defaults={
                'title': 'Institutional Supporter Model',
                'overview': '''Partner with NRI to provide comprehensive research indexing 
                and visibility for your institution's publications and researchers.''',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created Institutional Supporter page'))
            
            # Add pricing tiers
            PricingTier.objects.create(
                support_page=institutional_page,
                category='Small Institution (< 50 researchers)',
                npr_amount=25000.00,
                usd_amount=200.00,
                purpose='Annual institutional membership with basic analytics',
                order=1
            )
            PricingTier.objects.create(
                support_page=institutional_page,
                category='Medium Institution (50-200 researchers)',
                npr_amount=50000.00,
                usd_amount=400.00,
                purpose='Annual membership with advanced analytics and branding',
                order=2
            )
            PricingTier.objects.create(
                support_page=institutional_page,
                category='Large Institution (> 200 researchers)',
                npr_amount=100000.00,
                usd_amount=800.00,
                purpose='Premium membership with custom integrations and priority support',
                order=3
            )
            
            # Add benefits
            SupportBenefit.objects.create(
                support_page=institutional_page,
                title='Institutional Dashboard',
                description='Comprehensive analytics dashboard for your institution\'s research output',
                order=1
            )
            SupportBenefit.objects.create(
                support_page=institutional_page,
                title='Custom Branding',
                description='Feature your institution\'s logo and branding on researcher profiles',
                order=2
            )
            SupportBenefit.objects.create(
                support_page=institutional_page,
                title='API Access',
                description='Programmatic access to your institution\'s publication data',
                order=3
            )
            SupportBenefit.objects.create(
                support_page=institutional_page,
                title='Dedicated Support',
                description='Dedicated account manager and priority technical support',
                order=4
            )
            
            # Add why support points
            WhySupportPoint.objects.create(
                support_page=institutional_page,
                title='Increase Visibility',
                description='Enhance your institution\'s research visibility nationally and internationally',
                order=1
            )
            WhySupportPoint.objects.create(
                support_page=institutional_page,
                title='Track Impact',
                description='Monitor citations, collaborations, and research trends',
                order=2
            )
            WhySupportPoint.objects.create(
                support_page=institutional_page,
                title='Support Researchers',
                description='Provide your researchers with tools to showcase their work',
                order=3
            )
            
            self.stdout.write('  Added pricing tiers, benefits, and why support points')
        else:
            self.stdout.write(self.style.WARNING('⚠ Institutional Supporter page already exists'))

        # Create Sponsorship & Partnership Page
        sponsorship_page, created = SupportPage.objects.get_or_create(
            page_type='sponsorship_partnership',
            defaults={
                'title': 'Sponsorship & Partnership',
                'overview': '''Become a strategic partner in advancing research excellence 
                across Nepal. Support the platform while gaining visibility among Nepal's 
                research community.''',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created Sponsorship & Partnership page'))
            
            # Add sponsorship and partnership details directly to the page
            sponsorship_page.sponsorship_detail = '''
<h3>Corporate Sponsorship Benefits</h3>
<ul>
    <li>Logo placement on platform homepage and documentation</li>
    <li>Recognition in annual reports and newsletters</li>
    <li>Access to aggregated platform statistics</li>
    <li>Visibility among Nepal's research community</li>
</ul>
<p>Support NRI through corporate sponsorship and gain visibility among Nepal's research community.</p>
'''
            
            sponsorship_page.partnership_detail = '''
<h3>Partnership Opportunities</h3>
<ul>
    <li>API integration opportunities</li>
    <li>Co-branded research tools and features</li>
    <li>Joint events and webinars</li>
    <li>Collaborative research initiatives</li>
</ul>
<p>Partner with NRI to integrate research tools and services into our platform.</p>
<p><strong>Contact us to discuss sponsorship or partnership opportunities.</strong></p>
'''
            
            sponsorship_page.save()
            
            self.stdout.write('  Added sponsorship and partnership details')
        else:
            self.stdout.write(self.style.WARNING('⚠ Sponsorship & Partnership page already exists'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n✓ Setup complete!'))
        self.stdout.write(f'\nTotal Support Pages: {SupportPage.objects.count()}')
        self.stdout.write(f'Total Pricing Tiers: {PricingTier.objects.count()}')
        self.stdout.write(f'Total Benefits: {SupportBenefit.objects.count()}')
        self.stdout.write(f'Total Why Support Points: {WhySupportPoint.objects.count()}')
        self.stdout.write('\nYou can now access the support pages via the API!')
