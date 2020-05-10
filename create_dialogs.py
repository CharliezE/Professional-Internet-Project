import pickle


dialogs = {}


with open('dialogs.pickle', 'wb') as f:
    pickle.dump((dialogs), f)
