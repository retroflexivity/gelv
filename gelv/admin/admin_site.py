from django.contrib import admin
from django.urls import NoReverseMatch, reverse
from django.utils.text import capfirst


class CustomAdminSite(admin.AdminSite):
    def __init__(self, apps={}, *args, **kwargs):
        admin.AdminSite.__init__(self, *args, **kwargs)
        self.apps = apps

    def _generate_model_dict(self, model, model_admin, request):
        app_label = model._meta.app_label

        has_module_perms = model_admin.has_module_permission(request)
        if not has_module_perms:
            return

        perms = model_admin.get_model_perms(request)

        if True not in perms.values():
            return

        info = (app_label, model._meta.model_name)
        model_dict = {
            "model": model,
            "name": capfirst(model._meta.verbose_name_plural),
            "object_name": model._meta.object_name,
            "perms": perms,
            "admin_url": None,
            "add_url": None,
        }

        if perms.get("change") or perms.get("view"):
            model_dict["view_only"] = not perms.get("change")
            try:
                model_dict["admin_url"] = reverse(
                    "admin:%s_%s_changelist" % info, current_app=self.name
                )
            except NoReverseMatch:
                pass
        if perms.get("add"):
            try:
                model_dict["add_url"] = reverse(
                    "admin:%s_%s_add" % info, current_app=self.name
                )
            except NoReverseMatch:
                pass

        return model_dict

    def _build_app_dict(self, request, label=None):
        """
        Build the app dictionary. The optional `label` parameter filters models
        of a specific app.
        """
        app_dict = {}

        if label:
            models = {
                m: m_a
                for m, m_a in self._registry.items()
                if m._meta.app_label == label
            }
        else:
            models = self._registry

        app_dict = {}
        for app, model_list in self.apps.items():
            app_model_dicts = []
            for model in model_list:
                model_admin = models[model]
                model_dict = (self._generate_model_dict(model, model_admin, request))
                if model_dict:
                    app_model_dicts.append(model_dict)

            app_label = model._meta.app_label
            app_dict[app] = {
                "name": app,
                "app_label": app_label,
                "app_url": reverse(
                    "admin:app_list",
                    kwargs={"app_label": app_label},
                    current_app=self.name,
                ),
                "has_module_perms": model_admin.has_module_permission(request),
                "models": app_model_dicts,
            }

        return app_dict


admin_site = CustomAdminSite(name="customadmin")
