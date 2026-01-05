from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Author, Institution, AuthorStats


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


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Institution, InstitutionAdmin)
admin.site.register(AuthorStats, AuthorStatsAdmin)
