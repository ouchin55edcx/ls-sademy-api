from django.contrib import admin
from core.models import User, Admin, Collaborator, Client, Service, Template, Status, Order, Livrable, Review

# Register your models here.
admin.site.register(User)
admin.site.register(Admin)
admin.site.register(Collaborator)
admin.site.register(Client)
admin.site.register(Service)
admin.site.register(Template)
admin.site.register(Status)
admin.site.register(Order)
admin.site.register(Livrable)
admin.site.register(Review)
