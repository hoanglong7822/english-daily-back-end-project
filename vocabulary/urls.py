from django.urls import path

from .views import (
    UploadImageView,
    VocabularyCollectionDetailView,
    VocabularyCollectionListView,
    WordDetailView,
    WordListCreateView,
    WordBulkCreateView,
    GenerateAIWordsAPIView
)

urlpatterns = [
    # Upload ảnh
    path('upload-image/', UploadImageView.as_view(), name='upload-image'),

    # Collections CRUD
    path('collections/', VocabularyCollectionListView.as_view(), name='collection-list'),
    path('collections/<int:collection_id>/', VocabularyCollectionDetailView.as_view(), name='collection-detail'),

    # Words CRUD (nested under collection)
    path('collections/<int:collection_id>/words/', WordListCreateView.as_view(), name='word-list'),
    path('collections/<int:collection_id>/words/bulk/', WordBulkCreateView.as_view(), name='word-bulk-create'),
    path('collections/<int:collection_id>/words/<int:word_id>/', WordDetailView.as_view(), name='word-detail'),
        path(
        "collections/<int:collection_id>/generate-ai/",
        GenerateAIWordsAPIView.as_view(),
        name="generate-ai-words"
    ),
]
