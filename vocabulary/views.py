from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework import status
from .ai_service import (
    generate_collection_words
)

from django.conf import settings

import os
import uuid

from .models import VocabularyCollection, VocabularyCollectionWord
from .serializers import VocabularyCollectionSerializer, VocabularyCollectionWordSerializer,GenerateAIWordsSerializer


class VocabularyCollectionListView(APIView):
    """
    GET  /api/vocabulary/collections/
         Trả về tất cả collections của user đang đăng nhập.

    POST /api/vocabulary/collections/
         Tạo collection mới.
         Body: { name, description (optional) }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        collections = VocabularyCollection.objects.filter(
            user=request.user
        ).order_by('-created_at')
        serializer = VocabularyCollectionSerializer(collections, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = VocabularyCollectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def get_collection_or_404(user, collection_id):
    """Helper: lấy collection thuộc về user, trả về None nếu không tìm thấy."""
    try:
        return VocabularyCollection.objects.get(pk=collection_id, user=user)
    except VocabularyCollection.DoesNotExist:
        return None


class VocabularyCollectionDetailView(APIView):
    """
    GET    /api/vocabulary/collections/<collection_id>/
           Lấy chi tiết một collection.

    PUT    /api/vocabulary/collections/<collection_id>/
           Cập nhật toàn bộ collection.
           Body: { name, description }

    PATCH  /api/vocabulary/collections/<collection_id>/
           Cập nhật một phần collection.

    DELETE /api/vocabulary/collections/<collection_id>/
           Xóa collection (và toàn bộ words bên trong).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, collection_id):
        collection = get_collection_or_404(request.user, collection_id)
        if collection is None:
            return Response({'detail': 'Collection not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(VocabularyCollectionSerializer(collection).data)

    def put(self, request, collection_id):
        collection = get_collection_or_404(request.user, collection_id)
        if collection is None:
            return Response({'detail': 'Collection not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = VocabularyCollectionSerializer(collection, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, collection_id):
        collection = get_collection_or_404(request.user, collection_id)
        if collection is None:
            return Response({'detail': 'Collection not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = VocabularyCollectionSerializer(collection, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, collection_id):
        collection = get_collection_or_404(request.user, collection_id)
        if collection is None:
            return Response({'detail': 'Collection not found.'}, status=status.HTTP_404_NOT_FOUND)
        collection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WordListCreateView(APIView):
    """
    GET  /api/vocabulary/collections/<collection_id>/words/
         Lấy tất cả words trong collection.

    POST /api/vocabulary/collections/<collection_id>/words/
         Tạo word mới trong collection.
         Body: { english_word, vietnamese_meaning, pronunciation (optional) }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, collection_id):
        collection = get_collection_or_404(request.user, collection_id)
        if collection is None:
            return Response(
                {'detail': 'Collection not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        words = collection.words.order_by('-created_at')
        serializer = VocabularyCollectionWordSerializer(words, many=True)
        return Response(serializer.data)

    def post(self, request, collection_id):
        collection = get_collection_or_404(request.user, collection_id)
        if collection is None:
            return Response(
                {'detail': 'Collection not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Bulk create: body là array
        if isinstance(request.data, list):
            serializer = VocabularyCollectionWordSerializer(data=request.data, many=True)
            if serializer.is_valid():
                words = VocabularyCollectionWord.objects.bulk_create([
                    VocabularyCollectionWord(collection=collection, **item)
                    for item in serializer.validated_data
                ])
                result = VocabularyCollectionWordSerializer(words, many=True)
                return Response(result.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Single create: body là object
        serializer = VocabularyCollectionWordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(collection=collection)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WordBulkCreateView(APIView):
    """
    POST /api/vocabulary/collections/<collection_id>/words/bulk/
         Tạo nhiều words cùng lúc.
         Body: [
           { "english_word": "candidate", "vietnamese_meaning": "ứng viên", "pronunciation": "/ˈkændɪdət/", "word_type": "noun" },
           { "english_word": "confirm", "vietnamese_meaning": "xác nhận", "pronunciation": "/kənˈfɜːrm/", "word_type": "verb" }
         ]
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, collection_id):
        collection = get_collection_or_404(request.user, collection_id)
        if collection is None:
            return Response(
                {'detail': 'Collection not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not isinstance(request.data, list):
            return Response(
                {'detail': 'Expected a list of words.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(request.data) == 0:
            return Response(
                {'detail': 'Word list must not be empty.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = VocabularyCollectionWordSerializer(data=request.data, many=True)
        if serializer.is_valid():
            words = VocabularyCollectionWord.objects.bulk_create([
                VocabularyCollectionWord(collection=collection, **item)
                for item in serializer.validated_data
            ])
            result = VocabularyCollectionWordSerializer(words, many=True)
            return Response(result.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WordDetailView(APIView):
    """
    GET    /api/vocabulary/collections/<collection_id>/words/<word_id>/
           Lấy chi tiết một word.

    PUT    /api/vocabulary/collections/<collection_id>/words/<word_id>/
           Cập nhật toàn bộ word.
           Body: { english_word, vietnamese_meaning, pronunciation }

    PATCH  /api/vocabulary/collections/<collection_id>/words/<word_id>/
           Cập nhật một phần word.

    DELETE /api/vocabulary/collections/<collection_id>/words/<word_id>/
           Xóa word.
    """

    permission_classes = [IsAuthenticated]

    def get_word(self, request, collection_id, word_id):
        collection = get_collection_or_404(request.user, collection_id)
        if collection is None:
            return None, Response(
                {'detail': 'Collection not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            word = collection.words.get(pk=word_id)
            return word, None
        except VocabularyCollectionWord.DoesNotExist:
            return None, Response(
                {'detail': 'Word not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

    def get(self, request, collection_id, word_id):
        word, error = self.get_word(request, collection_id, word_id)
        if error:
            return error
        return Response(VocabularyCollectionWordSerializer(word).data)

    def put(self, request, collection_id, word_id):
        word, error = self.get_word(request, collection_id, word_id)
        if error:
            return error
        serializer = VocabularyCollectionWordSerializer(word, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, collection_id, word_id):
        word, error = self.get_word(request, collection_id, word_id)
        if error:
            return error
        serializer = VocabularyCollectionWordSerializer(word, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, collection_id, word_id):
        word, error = self.get_word(request, collection_id, word_id)
        if error:
            return error
        word.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UploadImageView(APIView):
    """
    POST /api/vocabulary/upload-image/
    Header: Authorization: Bearer <access_token>
    Content-Type: multipart/form-data
    Body: { image: <file> }

    Upload ảnh lên server, trả về URL để lưu vào image_url của word.
    Chỉ chấp nhận: jpg, jpeg, png, gif, webp.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    MAX_SIZE_MB = 5

    def post(self, request):
        image_file = request.FILES.get('image')

        if not image_file:
            return Response(
                {'detail': 'No image file provided.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Kiểm tra extension
        ext = image_file.name.rsplit('.', 1)[-1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            return Response(
                {'detail': f'File type not allowed. Allowed: {", ".join(self.ALLOWED_EXTENSIONS)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Kiểm tra kích thước (max 5MB)
        if image_file.size > self.MAX_SIZE_MB * 1024 * 1024:
            return Response(
                {'detail': f'File too large. Maximum size is {self.MAX_SIZE_MB}MB.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Tạo tên file unique để tránh trùng
        filename = f'{uuid.uuid4().hex}.{ext}'
        relative_path = os.path.join('vocabulary', 'words', filename)
        absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        # Tạo thư mục nếu chưa có
        os.makedirs(os.path.dirname(absolute_path), exist_ok=True)

        # Lưu file
        with open(absolute_path, 'wb') as f:
            for chunk in image_file.chunks():
                f.write(chunk)

        # Trả về URL đầy đủ
        image_url = request.build_absolute_uri(f'{settings.MEDIA_URL}{relative_path}')

        return Response({'image_url': image_url}, status=status.HTTP_201_CREATED)

class GenerateAIWordsAPIView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        collection_id
    ):

        serializer = (
            GenerateAIWordsSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        collection = get_object_or_404(
            VocabularyCollection,
            id=collection_id,
            user=request.user
        )

        total_words = serializer.validated_data[
            "total_words"
        ]

        level = serializer.validated_data[
            "level"
        ]

        try:

            words = generate_collection_words(
                collection_name=collection.name,
                collection_description=collection.description,
                total_words=total_words,
                level=level
            )

            return Response(
                {
                    "collection": {
                        "id": collection.id,
                        "name": collection.name,
                        "description": collection.description
                    },
                    "words": words
                },
                status=status.HTTP_200_OK
            )

        except Exception as error:

            return Response(
                {
                    "message": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )