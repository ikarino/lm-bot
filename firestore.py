import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from pprint import pprint

class MyFirestore:
    def __init__(self):
        # Use a service account
        cred = credentials.Certificate('firebase.json')
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def set_current_player_names(self, player_names: list):
        ref = self.db.collection('current').document('player_names')
        ref.set({
            f"{p['rank']:04d}": p['player_name']
            for p in player_names
        })

    def append_current_gifts(self, gifts: list):
        ref = self.db.collection('current').document('gifts')
        doc = ref.get()

        current = {}
        if doc.exists:
            current = doc.to_dict()
            
        length = len(current)
        for i, g in enumerate(gifts):
            current[f"{length + i:04d}"] = g
        ref.set(current)

    def get_current_players(self):
        doc = self.db.collection('current').document('player_names').get()
        return sorted(doc.to_dict().values())

    def get_current_gifts(self):
        doc = self.db.collection('current').document('gifts').get()
        return list(doc.to_dict().values())

    def remove_gifts(self):
        ref = self.db.collection('current').document('gifts')
        ref.set({})

    def save_as(self, collection):
        player_names = self.db.collection('current').document('player_names').get().to_dict()
        gifts = self.db.collection('current').document('gifts').get().to_dict()
        self.db.collection(collection).document('player_names').set(player_names)
        self.db.collection(collection).document('gifts').set(gifts)

    def get_result(self):
        players = self.get_current_players()
        gifts = self.get_current_gifts()

        result = {}
        for player in players:
            _gifts = [0]*5
            _pop_indexs = []

            # 集計
            for __index, __g in enumerate(gifts):
                __player_name = __g['player_name']
                __rank = __g['rank']
                if __player_name == player:
                    _gifts[__rank-1] += 1
                    _pop_indexs.append(__index)
            
            result[player] = _gifts
            # ヒットしたものは削除
            gifts = [g for i, g in enumerate(gifts) if i not in _pop_indexs]

        if gifts:
            result['Error'] = gifts

        return result

        
if __name__ == "__main__":
    mf = MyFirestore()
    # mf.set_current_player_names(players)
    # mf.append_current_gifts(gifts)
    # mf.append_current_gifts(gifts)
    print(mf.get_current_gifts())
    