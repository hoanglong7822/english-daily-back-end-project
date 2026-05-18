from django.db import models
from django.contrib.auth.models import User

class VocabularyCollection(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vocabulary_collections'
    )

    name = models.CharField(max_length=255)

    description = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'vocabulary_collections'

    def __str__(self):
        return self.name

class VocabularyCollectionWord(models.Model):
    collection = models.ForeignKey(
        VocabularyCollection,
        on_delete=models.CASCADE,
        related_name='words'
    )

    english_word = models.CharField(
        max_length=255
    )

    vietnamese_meaning = models.CharField(
        max_length=255
    )

    pronunciation = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'vocabulary_collection_words'

    def __str__(self):
        return self.english_word

class VocabularyStudySession(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vocabulary_study_sessions'
    )

    collection = models.ForeignKey(
        VocabularyCollection,
        on_delete=models.CASCADE,
        related_name='vocabulary_study_sessions'
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'vocabulary_study_sessions'

    def __str__(self):
        return f'Vocabulary Study Session #{self.id}'


class VocabularyStudyResult(models.Model):
    session = models.ForeignKey(
        VocabularyStudySession,
        on_delete=models.CASCADE,
        related_name='vocabulary_study_results'
    )

    vocabulary = models.ForeignKey(
        VocabularyCollectionWord,
        on_delete=models.CASCADE,
        related_name='vocabulary_study_results'
    )

    user_answer = models.CharField(
        max_length=255
    )

    is_correct = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'vocabulary_study_results'

    def __str__(self):
        return f'Vocabulary Study Result #{self.id}'