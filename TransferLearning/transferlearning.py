# -*- coding: utf-8 -*-
"""TransferLearning.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1YWmMjjVpLARrJKWWgTAORqKjM_s2RMVM

### PyTorch tutorial #1  
## TRANSFER LEARNING

Transfer learning is a machine learning method where a model developed for the first task is then used as the starting point for a model on a second task. Since it is relatively rare to have a dataset of sufficient size, in practice very few people train an entire CNN from scratch and it is common to pretrain a ConvNet on a very large dataset (ImageNet) and then use the ConvNet either as an initialization or a fixed feature extractor for the task of interest.


In This tutorial uses a subset of ImageNet as a dataset and a ResNet as the architecture.

Sources for this tutorial:
- [PyTorch.org](https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html)
- [Video Explanation](https://www.youtube.com/watch?v=t6oHGXt04ik)

## What do we need?
A future statement is a directive to the compiler that a particular module should be compiled. It helps to use syntax or semantics that will be available in a specified future release of Python where the feature becomes standard. A future statement must appear near the top of the module.
"""

from __future__ import print_function, division

import torch
import torch.nn as nn  #Contains the neural network layers
import torch.optim as optim  #A package implementing various optimization algorithms
from torch.optim import lr_scheduler  #A Learning rate schedule is a predefined framework that 
#adjusts the learning rate between epochs or iterations as the training progresses
import torch.backends.cudnn as cudnn  #torch.backends controls the behavior of various backends that PyTorch supports.
import numpy as np
import torchvision  #Torchvision provides many built-in datasets in the torchvision.datasets module,
#as well as utility classes for building your own datasets.
from torchvision import datasets, models, transforms
import matplotlib.pyplot as plt #a collection of command style functions that make matplotlib work like MATLAB.
import time #Python time module allows to work with time in Python
import os #provides functions for creating and removing a directory (folder), fetching its contents,
# changing and identifying the current directory, etc.
import copy #It means that any changes made to a copy of object do reflect in the original object.

"""## Hardware 

This flag allows you to enable the inbuilt cudnn auto-tuner to find the best algorithm to use for your hardware. Use it if your model does not change and your input sizes remain the same
"""

cudnn.benchmark = True

"""## Plotting
Turns on the interactive mode of matplotlib.pyplot, in which the graph display gets updated after each statement.
"""

plt.ion()

"""## The Problem
Train a model to classify ants and bees. We have about 120 training images each for ants and bees. There are 75 validation images for each class. Usually, this is a very small dataset to generalize upon, if trained from scratch. Since we are using transfer learning, the network has already learnet useful features and we should be able to generalize reasonably well.

### Data Augmentation & Normalization

- ### *transformers.compose* 
To chain the transformers together
- ### *transforms.RandomResizedCrop ( size, scale, ratio, interpolation)*  
Crop a random portion of image and resize it to a given size. 
  - size (int or sequence): expected output size of the crop, for each edge.
  - scale (tuple of python:float): Specifies the lower and upper bounds for the random area of the crop, before resizing. The scale is defined with respect to the area of the original image.
  - ratio (tuple of python:float): lower and upper bounds for the random aspect ratio of the crop, before resizing.
  - interpolation (InterpolationMode) – Desired interpolation enum defined by torchvision.transforms.InterpolationMode. Default is InterpolationMode.BILINEAR
- ### *transforms.RandomHorizontalFlip(p)*
  Horizontally flip the given image randomly with a given probability p. 
- ### *transforms.ToTensor()*
Transforms images loaded by Pillow into PyTorch tensors
- ### *transforms.Normalize(mean, std, inplace=False)*
Normalize a tensor image with mean and standard deviation. Not necessary, but helps the model to preform better.
  - mean (sequence): Sequence of means for each channel.
  - std (sequence): Sequence of standard deviations for each channel.
  - inplace (bool,optional): Bool to make this operation in-place.
- ### *transforms.Resize(size, interpolation=<InterpolationMode.BILINEAR: 'bilinear'>, max_size=None, antialias=None)*
Resize the input image to the given size.
  - size (sequence or int): Desired output size. 
  - interpolation (InterpolationMode): Desired interpolation enum defined by torchvision.transforms.InterpolationMode. 
  - max_size (int, optional): The maximum allowed for the longer edge of the resized image
  - antialias (bool, optional): antialias flag. If img is PIL Image, the flag is ignored and anti-alias is always used. If img is Tensor, the flag is False by default and can be set to True for InterpolationMode.BILINEAR only mode. This can help making the output for PIL images and tensors closer.
- ### *transforms.CenterCrop(size)*
Crops the given image at the center.
  - size (sequence or int): Desired output size of the crop. If size is an int instead of sequence like (h, w), a square crop (size, size) is made.
"""

# Data augmentation and normalization for training
# Just normalization for validation
data_transforms = {
    'train' : transforms.Compose([
                                  transforms.RandomResizedCrop(224), #augmenting
                                  transforms.RandomHorizontalFlip(), #augmenting
                                  transforms.ToTensor(), #pytorch can read it now
                                  transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                                  ]), #mean and std for 3 channels of RGB
    'val' : transforms.Compose([
                                transforms.Resize(256),
                                transforms.CenterCrop(224), #to get the actual object to classify
                                transforms.ToTensor(),
                                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}

#Add the dataset to the google drive and mount it.
data_dir = '/content/drive/MyDrive/Colab Notebooks/hymenoptera_data'

"""## Loading The Data
This [dataset](https://download.pytorch.org/tutorial/hymenoptera_data.zip) is a very small subset of imagenet. Use torchvision and torch.utils.data packages for loading the data. 

You have the `train` and `val` images and you pass in the path and transforms for each of them.

- ### *torchvision.datasets.ImageFolder()*  
A generic data loader
   - root (string): Root directory path.
   - transform (callable, optional): A function/transform that takes in an PIL image and returns a transformed version. E.g, transforms.RandomCrop
   - target_transform (callable, optional): A function/transform that takes in the target and transforms it.
- ### *os.path.join(path, *paths)*  
os.path module implements some useful functions on pathnames. Here it joins one or more path components intelligently.
"""

image_datasets = {x: datasets.ImageFolder(os.path.join(data_dir, x),
                                          data_transforms[x])
                  for x in ['train', 'val']} #creating a dictionary

image_datasets["val"] #to see the information

"""### Setting up the data loaders
- ### *torch.utils.data.DataLoader*  
Combines a dataset and a sampler, and provides an iterable over the given dataset.(basically sampling the data)

  - *batch_size=4*

    4 will work well since our dataset is small.

  - *shuffle=True*
  
    usually we turn the shuffle on because we want to shuffle data in every epoch so it doesn't learn the same pattern.(Makes the model more robust)
    - *num_workers*

    Number of subprocesses that are running. This will speed up the data loader.

"""

dataloaders = {x: torch.utils.data.DataLoader(image_datasets[x], batch_size=4,
                                             shuffle=True, num_workers=4)
              for x in ['train', 'val']}

"""## Dataset sizes

We will need the dataset sizes for calculating the loss and the accuracy when we are training. We can see here how many training and validation images we have.
"""

dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
dataset_sizes["train"], dataset_sizes["val"]

"""## Class Names

Category 0 is ants and category 1 is bees.
"""

class_names = image_datasets['train'].classes
class_names

"""## Device for Training
Even if you don't have an actual GPU, you can head to Colab and use the GPU there since it will speed up the process.
- ### *torch.device* 
An object representing the device on which a torch.Tensor is or will be allocated.(('cpu' or 'cuda'))
"""

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

"""## Visualizing a few Images

Visualizing a few training images so as to understand the data augmentations. We are defining a function to do the task.

- ### *inp = std * inp + mean*
Since we had a normalization step before, here we have to revert the image to normal. Otherwise, we will get an image w/ color channels all messed up.



"""

def imshow(inp, title=None):
    """Imshow for Tensor."""
    inp = inp.numpy().transpose((1, 2, 0)) #transposes the data (x,y,z)->(y,z,x)
    mean = np.array([0.485, 0.456, 0.406]) # Creates an array.
    std = np.array([0.229, 0.224, 0.225])
    inp = std * inp + mean #reverting the normalized image
    inp = np.clip(inp, 0, 1) #Clip (limit) the values in an array.
    plt.imshow(inp)
    if title is not None:
        plt.title(title)
    plt.pause(0.001)  # pause a bit so that plots are updated

"""Get a batch of training data.
- #### *next(iter(dataloaders))*
makes dataloader object to be a iterable and “next” helps it to iterate over it.
If your Dataset.__getitem__ returns multiple tensors, next(iter(loader)) will return a batch for each output.

The result:

- *torch.Size*:

 the batch size equal to 4, with 3 channels and an image of size 224*224
- *tensor*

  It will represent the class of images that will be visualized. (e.g. [0, 1, 1, 1] means first image is an ant the other 3 will be bees.)
"""

inputs, classes = next(iter(dataloaders['train']))
inputs.shape, classes

"""### Make a grid from batch
- ### *torchvision.utils.make_grid(tensor: Union[torch.Tensor, List[torch.Tensor]])*
Make a grid of images.
  - tensor (Tensor or list): 4D mini-batch Tensor of shape (B x C x H x W) or a list of images all of the same size.

"""

out = torchvision.utils.make_grid(inputs)

"""Use the function to visualize some training images.

The images are as we were expecting from the result of line 15.
"""

imshow(out, title=[class_names[x] for x in classes])

"""## Training the model
A general function to train a model.
- ### *since = time.time()*
To keep track of time. So that we can estimate how long it takes to train the model. It returns the time in seconds since the epoch.

- ### *best_model_wts = copy.deepcopy(model.state_dict())*
To keep the best model at every epoch.

  It will take a copy of the original object and will then recursively take a copy of the inner objects, i.e. all parameters of your model. The model structure will not be saved.

  Here you will initialize it and then at every epoch you will check the accuracy and overwrite it if there is a model with higher accuracy.

ResNet has some layers like batch normalization where you get different behaviour depending on whether you are in training or evaluation. Therefore, it is important to set the model to `model.train` or `model.eval` such that the model behaves exactly like you want.

- *Iterate over data*

  We also have to copy labels and inputs to GPU. to make sure data and labels are in the same device. This step is not necessary if you are using CPU.

- ### *optim.Optimizer.zero_grad(set_to_none=False)*
Sets the gradients of all optimized torch.Tensor s to zero.
  - *set_to_none=False*: instead of setting to zero, set the grads to None.

  If you forget to zero the gradient, it will accumulate the gradients and the backpropagation might not work properly.


- *statistics*

  The loss that you get is the average of the current batch. You multiply it with the batch size and you get the original loss.
"""

def train_model(model, criterion, optimizer, scheduler, num_epochs=25):
    since = time.time()

    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0
    
    #training loop
    for epoch in range(num_epochs):
        print(f'Epoch {epoch}/{num_epochs - 1}') #prints the current epoch we are in
        print('-' * 10)

        # Each epoch has a training and validation phase
        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()  # Set model to training mode
            else:
                model.eval()   # Set model to evaluate mode

            running_loss = 0.0 #initialize the loss to 0
            running_corrects = 0 #initialize the number of correct classifications to 0

            # Iterate over data.
            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device) #copy inputs to GPU
                labels = labels.to(device) #copy labels to GPU

                # zero the parameter gradients
                optimizer.zero_grad()

                # forward
                # track history if only in train
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels) #crossentropy loss

                    # backward + optimize only if in training phase
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                # statistics
                running_loss += loss.item() * inputs.size(0) #multiply the loss w/ batch size=4
                running_corrects += torch.sum(preds == labels.data)
            if phase == 'train':
                scheduler.step() #used for the model to converge faster
            
            #print loss and accuracy at the end of every epoch
            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

            # deep copy the model
            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict()) #overwriting the best model

        print()

    time_elapsed = time.time() - since
    print(f'Training complete in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s')
    print(f'Best val Acc: {best_acc:4f}')

    # load best model weights
    model.load_state_dict(best_model_wts)
    return model

"""## Visualizing the model predictions
Visualize what the model has learned after training.
It is a generic function to display predictions for a few images.

It basically, prints few instances of validation pictures and shows us what prediction the model has made. It is useful for evaluationg how our model performs.
"""

def visualize_model(model, num_images=6):
    was_training = model.training
    model.eval()
    images_so_far = 0
    fig = plt.figure()

    with torch.no_grad():
        for i, (inputs, labels) in enumerate(dataloaders['val']):
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)

            for j in range(inputs.size()[0]):
                images_so_far += 1
                ax = plt.subplot(num_images//2, 2, images_so_far)
                ax.axis('off')
                ax.set_title(f'predicted: {class_names[preds[j]]}')
                imshow(inputs.cpu().data[j])

                if images_so_far == num_images:
                    model.train(mode=was_training)
                    return
        model.train(mode=was_training)

"""## ResNet18 Architectutre
 Here I wanna check the initial architecture of the ResNet18 trained on the ImageNet dataset.

As you can see for the last fully connected layer we have:

(fc): Linear(in_features=512, out_features=1000, bias=True)

that takes 512 features and the output is the 1000 categories of the ImageNet.

<img title="ResNet18" alt="ResNet18" src="/content/drive/MyDrive/Colab Notebooks/ResNet-18-Architecture.png">
"""

models.resnet18(pretrained=True)

"""## Finetuning the convnet

We use the model ResNet18 and finetune it on our dataset.

- *model_ft = models.resnet18(pretrained=True)*

  Take the pretrained model and not just the architecture. It was trained on the ImageNet dataset.

- Fully Connected Layer

  Here we will map from `num_ftrs` which is equal to 512 to 2 categories of ants and bees. It replaces the previous architecture. Alternatively, it can be generalized to nn.Linear(num_ftrs, len(class_names)).
"""

model_ft = models.resnet18(pretrained=True)
num_ftrs = model_ft.fc.in_features #number of features in the FC layer

#Model's FC layer
model_ft.fc = nn.Linear(num_ftrs, 2)

#Copy the model to GPU
model_ft = model_ft.to(device)

criterion = nn.CrossEntropyLoss()

# Observe that all parameters are being optimized
optimizer_ft = optim.SGD(model_ft.parameters(), lr=0.001, momentum=0.9)

# Decay LR by a factor of 0.1 every 7 epochs
exp_lr_scheduler = lr_scheduler.StepLR(optimizer_ft, step_size=7, gamma=0.1)

num_ftrs #Just to see :)

"""## Train and evaluate
It should take around 15-25 min on CPU. On GPU though, it takes less than a minute.

The best validation accuracy will display at the result and you can check where exactly it is the case.
"""

model_ft = train_model(model_ft, criterion, optimizer_ft, exp_lr_scheduler,
                       num_epochs=25)

visualize_model(model_ft) #visualizing some of the results

"""## ConvNet as fixed feature extractor

Here, we need to freeze all the network except the final layer. We need to set `requires_grad = False` to freeze the parameters so that the gradients are not computed in backward().

We will just train the fully connected layer of the model and leave the base model as it is.

Training in this case on CPU wouldn't take as much time as needed for finetuning. Feature extractor is faster since you only have to compute the forward path and no backward step since you don't have to change all the weights in the ResNet.
"""

model_conv = torchvision.models.resnet18(pretrained=True)
for param in model_conv.parameters():
    param.requires_grad = False

# Parameters of newly constructed modules have requires_grad=True by default
num_ftrs = model_conv.fc.in_features
model_conv.fc = nn.Linear(num_ftrs, 2)

model_conv = model_conv.to(device)

criterion = nn.CrossEntropyLoss()

# Observe that only parameters of final layer are being optimized as
# opposed to before.
optimizer_conv = optim.SGD(model_conv.fc.parameters(), lr=0.001, momentum=0.9)

# Decay LR by a factor of 0.1 every 7 epochs
exp_lr_scheduler = lr_scheduler.StepLR(optimizer_conv, step_size=7, gamma=0.1)

"""## Train and evaluate

It performs better than the finetuning. It might be the case because the dataset is quite small.

Generally, If you have a large dataset like 1000-5000 images finetuning would be a better option. 
"""

model_conv = train_model(model_conv, criterion, optimizer_conv,
                         exp_lr_scheduler, num_epochs=25)

visualize_model(model_conv)

plt.ioff()
plt.show()