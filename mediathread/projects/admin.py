from django.contrib import admin
from django.contrib.auth.models import User
from mediathread.projects.models import Project


class ProjectAdmin(admin.ModelAdmin):
    search_fields = ("title",
                     "participants__last_name", "author__username",
                     "participants__last_name")

    list_display = ("title", "course", "author", "modified",
                    "date_submitted", "id", "project_type",
                    "response_view_policy")
    filter_horizontal = ('participants',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "author":
            kwargs["queryset"] = User.objects.all().order_by('username')
        return super(ProjectAdmin, self).formfield_for_foreignkey(db_field,
                                                                  request,
                                                                  **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "participants":
            kwargs["queryset"] = User.objects.all().order_by('username')
        return super(ProjectAdmin, self).formfield_for_manytomany(db_field,
                                                                  request,
                                                                  **kwargs)


admin.site.register(Project, ProjectAdmin)
