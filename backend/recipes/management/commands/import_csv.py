import csv
import os
from pathlib import Path
from django.conf import settings

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from recipes.models import Ingredient, Tag

FILES = [
    {
        'model': Ingredient,
        'file_path': f'{settings.BASE_DIR.parent}\\data\\ingredients.csv',
        'fieldnames': ['name', 'measurement_unit'],
    },
    {
        'model': Tag,
        'file_path': f'{settings.BASE_DIR}\\recipes\\data\\tags.csv',
        'fieldnames': ['name', 'slug'],
    },
]


class Command(BaseCommand):
    help = 'Import data from CSV files into the database'

    def handle(self, *args, **kwargs):
        for dic in FILES:
            model = dic.get('model')
            file_path = dic.get('file_path')
            fieldnames = dic.get('fieldnames')
            with open(file_path, 'r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file, fieldnames=fieldnames)
                for row in reader:
                    print(row)
                    model.objects.create(**row)
            self.stdout.write(self.style.SUCCESS('Данные загружены'))
