# -*- coding: utf-8 -*-
"""BuildingNetworkIntro.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1OdhDyhuryL_COmMqZWpT5y6UcsoTZb71

## Building the Neural Network
Find the related material [here](https://pythonprogramming.net/building-deep-learning-neural-network-pytorch/)
"""

#Loading the data
import torch
import torchvision
from torchvision import transforms, datasets


train = datasets.MNIST("", train=True, download=True, 
                       transform = transforms.Compose([
                           transforms.ToTensor()
                       ]))
test = datasets.MNIST("", train=False, download=True, 
                      transform = transforms.Compose([
                          transforms.ToTensor()
                      ]))

trainset = torch.utils.data.DataLoader(train, batch_size=10, shuffle=True)
testset= torch.utils.data.DataLoader(test, batch_size=10, shuffle=True)

"""## Importing libraries
In order to build the model we need to import new libraries. These two libraries are interchangeable. However, with functional you have to always pass parameters whereas with nn you would initialize things.
"""

import torch.nn as nn #Object Oriented programming
import torch.nn.functional as F #More like functions

"""## Building the model
The simplest neural network is fully connected, and feed-forward, meaning we go from input to output. First we create a class to make our model. We'll call this class *net* and this net will inhereit from the nn.Module class. The target here is to make three layers of 64 neurons for the hidden layers:
- *self* : access all the instances defined within a class, including its methods and attributes. 
- *super* corresponds to nn.module and *super(). __ init __()*  is running the initialization for nn., as well as whatever else we happen to put in *__ init__*
- Each of the *nn.Linear* layers expects the first parameter to be the input size, and the 2nd parameter is the output size.
  - The first layer takes in 28x28, because our images are 28x28 images of hand-drawn digits. A basic neural network is going to expect to have a flattened array, so not a 28x28, but instead a 1x784.
- *return F.log_softmax(x, dim=1)*
For the last layer we want an activation function such that one of the neurons fully fires therefore we are using softmax. 
  - *dim=1*: Is the dimension on which we want to apply softmax. It means which thing is the probability distribution that we want to sum to one.
  (dim=0 would mean distributing among the batches)  
   💡 Always use it w/ dim=1 it's hard to explain.
"""

class Net(nn.Module):

  def __init__(self):
    super().__init__()
    #Defining the fully connected layers
    self.fc1 = nn.Linear(28*28, 64)
    self.fc2 = nn.Linear(64, 64)
    self.fc3 = nn.Linear(64, 64)
    self.fc4 = nn.Linear(64, 10)
    #Since we have 10 classes the last layer's output has 10 neurons.

  #Defining the interaction between the layers
  def forward(self, x):
    #First x is going to pass through all the layers
    #For the first 3 layers there will be a relu activation function
    #For the last layer(on the 10 classes) we will have softmax
    x = F.relu(self.fc1(x))
    x = F.relu(self.fc2(x))
    x = F.relu(self.fc3(x)) 
    x = self.fc4(x)
    return F.log_softmax(x, dim=1)

#Define the network    
net= Net()
print(net)

"""## Passing data to the network
At this point the neural network is ready and we want to pass data to it.
- *X.view(-1,28 * 28)

-1 suggests "any size". It's a handy way for that bit to be variable. In this case, the variable part is how many "samples" we'll pass through.


"""

#Creatin a random image
#Mimicing the actual images we have
X = torch.randn((28,28))
#The network wants flattened input
X = X.view(-1,28*28)
output = net(X)
output

"""The output is a tensor that contains a tensor of our 10 possible classes, the actual predictions for the numbers.
- *grad_fn*  
stands for the gradient fuction. and calculating how far off were we.
"""