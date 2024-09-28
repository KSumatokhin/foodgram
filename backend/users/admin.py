from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import MyUser

# UserAdmin.list_display += ('role', )
# UserAdmin.list_editable += ('role', )
# UserAdmin.fieldsets += (
#     ('Extra Fields', {'fields': ('role', 'bio')}),
# )

admin.site.register(MyUser, UserAdmin)
