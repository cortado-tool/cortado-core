import glob
import os
import pm4py


class LpmDiscovererLoadExternalModels:
    def __init__(self, directory):
        self.directory = directory

    def discover_lpms(self, _):
        model_filenames = glob.glob(os.path.join(self.directory, "*.pnml"))
        models = []

        for model_filename in model_filenames:
            model = pm4py.read_pnml(model_filename)
            models.append((model, None))

        return models
