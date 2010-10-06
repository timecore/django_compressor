import os.path
import inspect

import django.conf
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import get_storage_class
from django.core.files import File

from compressor.conf import settings

class CompressorFileStorage(FileSystemStorage):
    """
    Standard file system storage for files handled by django-compressor.

    The defaults for ``location`` and ``base_url`` are ``COMPRESS_ROOT`` and
    ``COMPRESS_URL``.

    """
    def __init__(self, location=None, base_url=None, *args, **kwargs):
        if location is None:
            location = settings.MEDIA_ROOT
        if base_url is None:
            base_url = settings.MEDIA_URL
        super(CompressorFileStorage, self).__init__(location, base_url,
                                                    *args, **kwargs)

class AppSavvyCompressorFileStorage(CompressorFileStorage):
    """
    App Based file system storage for files handled by django-compressor.

    This storage tries to use the project's media path first. If not found,
    then it will try every installed app (in app reverse order, as to respect
    app precedence). If none found it returns false.

    The defaults for ``location`` and ``base_url`` are ``COMPRESS_ROOT`` and
    ``COMPRESS_URL``.

    """
    def __init__(self, location=None, base_url=None, *args, **kwargs):
        if location is None:
            location = settings.MEDIA_ROOT
        if base_url is None:
            base_url = settings.MEDIA_URL
        super(AppSavvyCompressorFileStorage, self).__init__(location,
                                                            base_url,
                                                            *args,
                                                            **kwargs)

    def _open(self, name, mode='rb'):
        if os.path.exists(os.path.join(self.location, name)):
            return super(AppSavvyCompressorFileStorage, self) \
                                                ._open(name, mode)

        paths = self.get_media_paths()
        for app, media_path in paths:
            file_path = os.path.join(media_path, name)
            if os.path.exists(file_path):
                return File(open(file_path, mode))

        raise ValueError('The file with name %s could not be found in the project MEDIA_ROOT or any of the installed apps media folders.' % name)

    def source_path(self, name):
        if os.path.exists(os.path.join(self.location, name)):
            return os.path.join(self.location, name)

        paths = self.get_media_paths()
        for app, media_path in paths:
            file_path = os.path.join(media_path, name)
            if os.path.exists(file_path):
                return file_path

    def exists(self, name):
        if os.path.exists(os.path.join(self.location, name)):
            return True

        paths = self.get_media_paths()

        for app, media_path in paths:
            if os.path.exists(os.path.join(media_path, name)):
                return True

        return False

    def get_media_paths(self):
        paths = []
        for app in reversed(django.conf.settings.INSTALLED_APPS):
            module = self.import_app(app)
            module_path = os.path.dirname(inspect.getfile(module))
            media_path = os.path.join(module_path, 'media')
            paths.append((app, media_path))
        return paths

    def import_app(self, appname):
        main_module = __import__(appname)
        if not "." in appname:
            return main_module

        return reduce(getattr, appname.split('.')[1:], main_module)
