from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Author, Institution


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


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Institution, InstitutionAdmin)
