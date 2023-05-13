from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm
from django.contrib.auth.models import User


def login_user(request):
    if request.method=="POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('factory-home')

        else:
            messages.success(request,("Sorry, username or password was incorrect. Try Again.."))
            return redirect('login')
    
    return render(request, 'users/login.html',{})

def logout_user(request):
    logout(request)
    return render(request, 'users/login.html')
    

def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        username=request.POST['username']
        if form.is_valid():
            form.save()
            username=form.cleaned_data.get('username')
            messages.success(request, f'Your account has been created {username} ! You are now able to login')
            return redirect('login')
        elif User.objects.filter(username=username).exists():
            messages.success(request, f'A user with that username already exists.')
            return redirect('register')
        elif len(str(form.cleaned_data.get('password1'))) < 8:
            messages.success(request, f'Password must be at least 8 characters long.')
            return redirect('register')
        else :
            messages.success(request, f'Passwords do not match.')
            return redirect('register')
          
    else:
        form = SignUpForm()
    return render(request, 'users/register.html',{'form':form})

@login_required
def profile(request):
    return render(request, 'users/profile.html')