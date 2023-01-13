import torch
import torchvision as tv

resnets = {
            18:tv.models.resnet18,
            34:tv.models.resnet34,
            50:tv.models.resnet50,
            101:tv.models.resnet101,
            152:tv.models.resnet152
        }

def build_resnet(resnet_version=50, num_classes=1000):
    model = resnets[resnet_version]()
    linear_size = list(model.children())[-1].in_features
    model.fc = torch.nn.Linear(linear_size, num_classes)
    return model
    