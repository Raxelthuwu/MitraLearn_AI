from .base import *
import os
from dotenv import load_dotenv

load_dotenv()

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'mingenially_learn',
        'CLIENT': {
            'host': os.environ.get('MONGODB_URI'),
        },
    }
}

CHROMA_PATH = os.environ.get("CHROMA_PATH", "chroma_db")