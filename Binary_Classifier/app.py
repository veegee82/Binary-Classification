from flask import Flask
from flask import request
from Binary_Classifier.inferencer import Inferencer, Inferencer_Params
from tfcore.interfaces.IPipeline_Inferencer import IPipeline_Inferencer_Params, IPipeline_Inferencer
from tfcore.utilities.preprocessing import Preprocessing
import gflags
import os
import sys
import imageio
import numpy as np

app = Flask(__name__)




def get_filename(idx, filename='', decimals=5):
    for n in range(decimals, -1, -1):
        if idx < pow(10, n):
            filename += '0'
        else:
            filename += str(idx)
            break
    return filename + '.png'

class Pipeline_Inferencer_Params(IPipeline_Inferencer_Params):

    def __init__(self,
                 data_dir_y,
                 data_dir_x=''):
        super().__init__(data_dir_y=data_dir_y, data_dir_x=data_dir_x)


class Pipeline_Inferencer(IPipeline_Inferencer):

    def __init__(self, inferencer, params, pre_processing):
        super().__init__(inferencer, params, pre_processing)

    def get_element(self, idx):

        try:
            img_x = imageio.imread(self.files_x[idx])
            img_y = self.files_x[idx].count('good')
        except FileNotFoundError:
            raise FileNotFoundError(' [!] File not found of data-set x')

        if self.pre_processing is not None:
            img_x, _ = self.pre_processing.run(img_x, None)

        return img_x, np.asarray(img_y)

@app.route('/predict')
def predict():
    url = request.args.get('image_url')
    return url

    flags = gflags.FLAGS
    gflags.DEFINE_string("dataset", "../Data/", "Dataset path")
    gflags.DEFINE_string("outdir", "../../../Data/Results/Horse2Zebra_AtoB", "Output path")
    gflags.DEFINE_string("model_dir", "Models_Deevio_Nailgun", "Model directory")


    flags(sys.argv)

    model_params = Inferencer_Params(image_size=224 / 2,
                                         model_path=flags.model_dir)
    model_inferencer = Inferencer(model_params)

    pre_processing = Preprocessing()
    pre_processing.add_function_x(Preprocessing.Central_Crop(size=(960, 960)).function)
    pre_processing.add_function_x(Preprocessing.Crop_by_Center(treshold=32, size=(224 * 2, 224 * 2)).function)
    pre_processing.add_function_x(Preprocessing.DownScale(factors=4).function)
    img_x, _ = pre_processing.run(img_x, None)

    pipeline_params = Pipeline_Inferencer_Params(data_dir_x=os.path.join(flags.dataset, 'train'),
                                                     data_dir_y=None)
    pipeline = Pipeline_Inferencer(inferencer=model_inferencer, params=pipeline_params, pre_processing=pre_processing)
    probs = pipeline.run()
    label = np.argmax(probs)
    labels = 'bad' if label == 0 else 'good'
    return_string = 'Label: ' + labels + ' Propabilitys: ' +  str(probs)
    return return_string

if __name__ == "__main__":
  app.run(host="localhost", debug=True)