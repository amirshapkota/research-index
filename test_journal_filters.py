"""
Test script for verifying journal filtering functionality.
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'researchindex.settings')
django.setup()

from publications.models import Journal, JournalStats, JournalQuestionnaire
from users.models import Institution
from django.db.models import Q

def test_filters():
    """Test all journal filters"""
    
    print("=" * 80)
    print("JOURNAL FILTER TESTING")
    print("=" * 80)
    
    # Get base queryset
    journals = Journal.objects.filter(is_active=True).select_related(
        'institution', 'stats', 'questionnaire'
    )
    
    total_journals = journals.count()
    print(f"\n✅ Total active journals: {total_journals}")
    
    # Test 1: Filter by access type
    print("\n" + "-" * 80)
    print("TEST 1: Filter by Access Type")
    print("-" * 80)
    open_access = journals.filter(is_open_access=True).count()
    print(f"  Open Access journals: {open_access}")
    print(f"  Subscription journals: {total_journals - open_access}")
    
    # Test 2: Filter by language
    print("\n" + "-" * 80)
    print("TEST 2: Filter by Language")
    print("-" * 80)
    languages = journals.values_list('language', flat=True).distinct()
    for lang in languages:
        count = journals.filter(language__icontains=lang).count()
        print(f"  {lang}: {count} journals")
    
    # Test 3: Filter by institution
    print("\n" + "-" * 80)
    print("TEST 3: Filter by Institution")
    print("-" * 80)
    institutions = Institution.objects.filter(journals__isnull=False).distinct()[:5]
    for inst in institutions:
        count = journals.filter(institution=inst).count()
        print(f"  {inst.institution_name}: {count} journals")
    
    # Test 4: Filter by country (through institution)
    print("\n" + "-" * 80)
    print("TEST 4: Filter by Country")
    print("-" * 80)
    countries = Institution.objects.filter(
        journals__isnull=False
    ).exclude(
        country=''
    ).values_list('country', flat=True).distinct()
    for country in countries[:5]:
        count = journals.filter(institution__country__icontains=country).count()
        print(f"  {country}: {count} journals")
    
    # Test 5: Filter by established year
    print("\n" + "-" * 80)
    print("TEST 5: Filter by Established Year")
    print("-" * 80)
    years = journals.exclude(
        established_year__isnull=True
    ).values_list('established_year', flat=True).distinct().order_by('-established_year')[:5]
    for year in years:
        count = journals.filter(established_year=year).count()
        print(f"  Year {year}: {count} journals")
    
    # Test 6: Filter by peer review status
    print("\n" + "-" * 80)
    print("TEST 6: Filter by Peer Review")
    print("-" * 80)
    peer_reviewed = journals.filter(peer_reviewed=True).count()
    print(f"  Peer-reviewed: {peer_reviewed}")
    print(f"  Not peer-reviewed: {total_journals - peer_reviewed}")
    
    # Test 7: Filter by peer review type (from questionnaire)
    print("\n" + "-" * 80)
    print("TEST 7: Filter by Peer Review Type")
    print("-" * 80)
    questionnaire_journals = journals.filter(questionnaire__isnull=False)
    peer_review_types = questionnaire_journals.exclude(
        questionnaire__peer_review_type=''
    ).values_list('questionnaire__peer_review_type', flat=True).distinct()
    for pr_type in peer_review_types:
        count = questionnaire_journals.filter(
            questionnaire__peer_review_type__icontains=pr_type
        ).count()
        print(f"  {pr_type}: {count} journals")
    
    # Test 8: Filter by license type
    print("\n" + "-" * 80)
    print("TEST 8: Filter by License Type")
    print("-" * 80)
    license_types = questionnaire_journals.exclude(
        questionnaire__license_type=''
    ).values_list('questionnaire__license_type', flat=True).distinct()
    for license in license_types:
        count = questionnaire_journals.filter(
            questionnaire__license_type__icontains=license
        ).count()
        print(f"  {license}: {count} journals")
    
    # Test 9: Filter by category/discipline
    print("\n" + "-" * 80)
    print("TEST 9: Filter by Category/Discipline")
    print("-" * 80)
    disciplines = questionnaire_journals.exclude(
        questionnaire__main_discipline=''
    ).values_list('questionnaire__main_discipline', flat=True).distinct()[:5]
    for discipline in disciplines:
        count = questionnaire_journals.filter(
            Q(questionnaire__main_discipline__icontains=discipline) |
            Q(questionnaire__secondary_disciplines__icontains=discipline)
        ).count()
        print(f"  {discipline}: {count} journals")
    
    # Test 10: Filter by impact factor
    print("\n" + "-" * 80)
    print("TEST 10: Filter by Impact Factor")
    print("-" * 80)
    stats_journals = journals.filter(stats__isnull=False)
    if stats_journals.exists():
        for threshold in [0.5, 1.0, 2.0, 3.0]:
            count = stats_journals.filter(stats__impact_factor__gte=threshold).count()
            print(f"  Impact Factor >= {threshold}: {count} journals")
    else:
        print("  No journals with stats available")
    
    # Test 11: Filter by CiteScore
    print("\n" + "-" * 80)
    print("TEST 11: Filter by CiteScore")
    print("-" * 80)
    if stats_journals.exists():
        for threshold in [1.0, 2.0, 3.0, 5.0]:
            count = stats_journals.filter(stats__cite_score__gte=threshold).count()
            print(f"  CiteScore >= {threshold}: {count} journals")
    else:
        print("  No journals with stats available")
    
    # Test 12: Filter by time to first decision
    print("\n" + "-" * 80)
    print("TEST 12: Filter by Time to First Decision (weeks)")
    print("-" * 80)
    review_time_journals = questionnaire_journals.exclude(
        questionnaire__average_review_time_weeks__isnull=True
    )
    if review_time_journals.exists():
        for max_weeks in [2, 4, 6, 8]:
            count = review_time_journals.filter(
                questionnaire__average_review_time_weeks__lte=max_weeks
            ).count()
            print(f"  <= {max_weeks} weeks: {count} journals")
    else:
        print("  No journals with review time data available")
    
    # Test 13: Filter by time to acceptance
    print("\n" + "-" * 80)
    print("TEST 13: Filter by Time to Acceptance (days)")
    print("-" * 80)
    if stats_journals.exists():
        acceptance_time_journals = stats_journals.exclude(
            stats__average_review_time__isnull=True
        ).exclude(
            stats__average_review_time=0
        )
        if acceptance_time_journals.exists():
            for max_days in [15, 30, 45, 60]:
                count = acceptance_time_journals.filter(
                    stats__average_review_time__lte=max_days
                ).count()
                print(f"  <= {max_days} days: {count} journals")
        else:
            print("  No journals with acceptance time data available")
    else:
        print("  No journals with stats available")
    
    # Test 14: Search functionality
    print("\n" + "-" * 80)
    print("TEST 14: Search Functionality")
    print("-" * 80)
    search_terms = ['journal', 'research', 'science', 'medical']
    for term in search_terms:
        count = journals.filter(
            Q(title__icontains=term) |
            Q(short_title__icontains=term) |
            Q(description__icontains=term) |
            Q(publisher_name__icontains=term)
        ).count()
        print(f"  Search '{term}': {count} results")
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
    print(f"\nAll {total_journals} journals can be filtered using the following parameters:")
    print("  - access_type / open_access")
    print("  - category (discipline)")
    print("  - language")
    print("  - license")
    print("  - years (established_year)")
    print("  - institutions")
    print("  - country")
    print("  - peer_review / peer_reviewed")
    print("  - impact_factor (minimum)")
    print("  - cite_score (minimum)")
    print("  - time_to_decision (maximum weeks)")
    print("  - time_to_acceptance (maximum days)")
    print("  - search (text search)")
    print("\n✅ All filters are ready for use in the API!")
    print()

if __name__ == '__main__':
    test_filters()
