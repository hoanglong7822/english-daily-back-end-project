from rest_framework import serializers

from .models import VocabularyCollection, VocabularyCollectionWord


class VocabularyCollectionSerializer(serializers.ModelSerializer):
    word_count = serializers.IntegerField(source='words.count', read_only=True)

    class Meta:
        model = VocabularyCollection
        fields = ('id', 'name', 'description', 'word_count', 'created_at')
        read_only_fields = ('id', 'word_count', 'created_at')


class VocabularyCollectionWordSerializer(serializers.ModelSerializer):
    word_type_display = serializers.CharField(source='get_word_type_display', read_only=True)

    class Meta:
        model = VocabularyCollectionWord
        fields = ('id', 'english_word', 'vietnamese_meaning', 'pronunciation', 'word_type', 'word_type_display', 'image_url', 'created_at')
        read_only_fields = ('id', 'created_at')
        
class GenerateAIWordsSerializer(
    serializers.Serializer
):

    total_words = serializers.IntegerField(
        default=20,
        min_value=1,
        max_value=100
    )

    level = serializers.ChoiceField(
        choices=[
            "beginner",
            "intermediate",
            "advanced"
        ],
        default="beginner"
    )