from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdmin, IsArtist, IsPromoter, IsFan

class AdminOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response({"message": "Welcome Admin!"})


class PromoterOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsPromoter]

    def get(self, request):
        return Response({"message": "Welcome Promoter!"})


class ArtistOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsArtist]

    def get(self, request):
        return Response({"message": "Welcome Artist!"})


class FanOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsFan]

    def get(self, request):
        return Response({"message": "Welcome Fan!"})
