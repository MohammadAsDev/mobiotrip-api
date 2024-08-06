from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from django.conf import settings

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import pickle
import networkx as nx

from .serializers import *


cache = settings.SYSTEM_CACHE


# Create your views here.
class PredictPathView(APIView):

    GRAPH_NAME = "road-chesapeake"
    MODEL_PATH = settings.PROJECT_ROOT + "/main_svm_model.pt"

    permission_classes = [IsAdminUser,]

    def predict_path(self , src , dst):
        path_stack = [src]
        visited_nodes = set()
        current_node = str(src)
        dst = str(dst)

        found = False

        while not found:    # 'till we don't get the destination
            if current_node not in visited_nodes:
                for node in list(self.graph[current_node]):    # getting all neighbors
                    if node == dst:
                        path_stack.append(node)
                        current_node = node
                        found = True
                        break
                    
                    connectivity = self.calc_connectivity(self.embs[int(node)] , self.embs[int(dst)])
                    pred_dist = self.svm_model.predict(connectivity)[0]
                    cache.zadd("Astar-score" , {str(node) : int(pred_dist)})
                
                visited_nodes.add(current_node)
            
            if found:
                continue

            min_item = cache.zpopmin("Astar-score") # no left items to traverse
            if not min_item:
                return []
            
            min_item = min_item[0]
            min_node = str(min_item[0])    # node_id, score 
            path_stack.append(min_node)
            current_node = min_node

        path = [int(dst)]
        end_node = dst
        for node in path_stack[-2::-1]:
            if str(end_node) in self.graph[str(node)]:
                path.append(int(node))
                end_node = node
        
        if str(path[-1]) != str(src):
            return []
        
        path.reverse()
        return path



    def predict_distance(self , src , dist):
        connectivity = self.calc_connectivity(self.embs[int(src)] , self.embs[int(dist)])
        return self.svm_model.predict(connectivity)



    def read_embs(self) -> pd.DataFrame:
        scaler = MinMaxScaler(feature_range=(0,1))
        
        emb_file = settings.PROJECT_ROOT +  "/{}.emb".format(self.GRAPH_NAME)
        emb_lines = open(emb_file , "r").readlines()[1:]
        emb_dict = {}
        for line in emb_lines:
            emb = line.split(" ")
            emb_dict[int(emb[0])] = np.array(emb[1:] , dtype=np.float32)
        
        scaler.fit(np.array(list(emb_dict.values())))
        emb_dict = {key : scaler.transform(val.reshape(1 , -1)).reshape(1, -1) for key, val in emb_dict.items()}

        return emb_dict

    def generate_graph(self):
        graph_path = settings.PROJECT_ROOT + "/{}.edgelist".format(self.GRAPH_NAME)
        return nx.read_edgelist(graph_path , create_using=nx.DiGraph)

    
    def calc_connectivity(self, src_embs, dst_embs) -> np.array:
        conv  = np.array((src_embs + dst_embs) / 2).reshape(1 , -1)
        return conv

    def post(self, request, format=None):
        serializer_class = PredictPathSerializer(data=request.data)
        if serializer_class.is_valid():
            model_path = self.MODEL_PATH

            self.graph = self.generate_graph()
            self.svm_model = pickle.load(open(model_path , "rb"))
            self.embs = self.read_embs()

            src , dst = int(serializer_class.data["src_node_id"]) , int(serializer_class.data["dst_node_id"])
            return Response({"predicted_path" : self.predict_path(src , dst)})

        return Response(serializer_class.errors)