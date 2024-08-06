from rest_framework import serializers

class PredictPathSerializer(serializers.Serializer):
    src_node_id = serializers.IntegerField()
    dst_node_id = serializers.IntegerField()