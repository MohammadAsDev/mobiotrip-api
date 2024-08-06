# MobioTrip (Still Working on it 😊)

## What is MobioTrip?
  In Simple Words, MobioTrip is a trip managment project, but it can be used for any movement operations.
  This project is distributed into different components where which one is responsible on a specific task.
  For now these components are still under testing, and in the next weeks it will published on my account.

  This repo contains the API for the whole system, The system interface is built using Django Framework.

## How does it work? 
  As i said above, This is the API of the system. The architecture design that have been used to build the system is:
    **Event-Driven Micro-Service Architecture**
  i've used this architecture to give the system higher availability and scalability.

  The event broker that i've been used is __Apache kafka__ , also the main system memory (shared between all
  micro-services to store the system's current state) is __Redis__. 

## To build this repo:
I don't like the `requirements.txt` file, because it may have many conflicts 😵.
For this reason, just install the following liberaries, and everything gonna be alright.

## Install this project on your device:
1. Build your own virtual environemnt `python3 -m venv (your_env)`
2. Install the following tools 

### [Django](https://www.djangoproject.com/)  (The main framework)
For Linux devices:
> python -m pip install Django==5.0.4

For Windows devices:
> py -m pip install Django==5.0.4

### [MySQL Client](https://pypi.org/project/mysqlclient/)
> pip install mysqlclient

### [Django Rest Framework(DRF)](https://www.django-rest-framework.org/)
the main liberary:
> pip install djangorestframework

to build convenient filtering system
> pip install django-filter

### [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/)
> pip install djangorestframework-simplejwt

### [Django CORS](https://pypi.org/project/django-cors-headers/)
> pip install django-cors-headers

### [DRF-yasg](https://github.com/axnsan12/drf-yasg/) 
This is a swagger-based liberary for DRF 
> pip install -U drf-yasg
