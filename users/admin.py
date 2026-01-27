from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Author, Institution, AuthorStats, InstitutionStats, AdminStats, Follow


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'user_type', 'is_staff', 'is_active', 'created_at']
    list_filter = ['user_type', 'is_staff', 'is_active']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('User Type', {'fields': ('user_type',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'user_type', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ['email']
    ordering = ['email']


class AuthorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'title', 'email', 'institute', 'designation']
    search_fields = ['full_name', 'user__email', 'institute']
    list_filter = ['title', 'institute']
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'


class InstitutionAdmin(admin.ModelAdmin):
    list_display = ['institution_name', 'email']
    search_fields = ['institution_name', 'user__email']
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'


class AuthorStatsAdmin(admin.ModelAdmin):
    list_display = [
        'author_name',
        'h_index',
        'i10_index',
        'total_citations',
        'total_publications',
        'total_reads',
        'last_updated'
    ]
    search_fields = ['author__full_name', 'author__user__email']
    list_filter = ['last_updated']
    readonly_fields = [
        'h_index',
        'i10_index',
        'total_citations',
        'total_reads',
        'total_downloads',
        'recommendations_count',
        'total_publications',
        'average_citations_per_paper',
        'last_updated',
        'created_at',
    ]
    
    def author_name(self, obj):
        return obj.author.full_name
    author_name.short_description = 'Author'
    
    actions = ['recalculate_stats']
    
    def recalculate_stats(self, request, queryset):
        """Admin action to recalculate stats for selected authors"""
        count = 0
        for stats in queryset:
            stats.update_stats()
            count += 1
        self.message_user(request, f'Successfully recalculated stats for {count} author(s).')
    recalculate_stats.short_description = 'Recalculate selected author statistics'


class InstitutionStatsAdmin(admin.ModelAdmin):
    list_display = [
        'institution_name',
        'total_publications',
        'total_citations',
        'total_authors',
        'total_reads',
        'last_updated'
    ]
    search_fields = ['institution__institution_name', 'institution__user__email']
    list_filter = ['last_updated']
    readonly_fields = [
        'total_publications',
        'total_citations',
        'average_citations_per_paper',
        'total_reads',
        'total_downloads',
        'recommendations_count',
        'total_authors',
        'last_updated',
        'created_at',
    ]
    
    def institution_name(self, obj):
        return obj.institution.institution_name
    institution_name.short_description = 'Institution'
    
    actions = ['recalculate_stats']
    
    def recalculate_stats(self, request, queryset):
        """Admin action to recalculate stats for selected institutions"""
        count = 0
        for stats in queryset:
            stats.update_stats()
            count += 1
        self.message_user(request, f'Successfully recalculated stats for {count} institution(s).')
    recalculate_stats.short_description = 'Recalculate selected institution statistics'


class AdminStatsAdmin(admin.ModelAdmin):
    list_display = [
        'admin_email',
        'total_users',
        'total_publications',
        'published_count',
        'total_citations',
        'last_updated'
    ]
    search_fields = ['user__email']
    list_filter = ['last_updated']
    readonly_fields = [
        'total_users',
        'total_authors',
        'total_institutions',
        'total_publications',
        'published_count',
        'draft_count',
        'total_citations',
        'total_reads',
        'total_downloads',
        'total_journals',
        'total_topics',
        'last_updated',
        'created_at',
    ]
    
    def admin_email(self, obj):
        return obj.user.email
    admin_email.short_description = 'Admin'
    
    actions = ['recalculate_stats']
    
    def recalculate_stats(self, request, queryset):
        """Admin action to recalculate system stats"""
        count = 0
        for stats in queryset:
            stats.update_stats()
            count += 1
        self.message_user(request, f'Successfully recalculated stats for {count} admin(s).')
    recalculate_stats.short_description = 'Recalculate system statistics'


class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower_email', 'follower_type', 'following_email', 'following_type', 'created_at']
    search_fields = ['follower__email', 'following__email']
    list_filter = ['follower__user_type', 'following__user_type', 'created_at']
    readonly_fields = ['created_at']
    raw_id_fields = ['follower', 'following']
    
    def follower_email(self, obj):
        return obj.follower.email
    follower_email.short_description = 'Follower'
    
    def follower_type(self, obj):
        return obj.follower.user_type
    follower_type.short_description = 'Follower Type'
    
    def following_email(self, obj):
        return obj.following.email
    following_email.short_description = 'Following'
    
    def following_type(self, obj):
        return obj.following.user_type
    following_type.short_description = 'Following Type'


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Institution, InstitutionAdmin)
admin.site.register(AuthorStats, AuthorStatsAdmin)
admin.site.register(InstitutionStats, InstitutionStatsAdmin)
admin.site.register(AdminStats, AdminStatsAdmin)
admin.site.register(Follow, FollowAdmin)
