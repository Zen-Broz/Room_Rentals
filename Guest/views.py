from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.template import loader
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from Guest.tokens import account_activation_token
from django.core.paginator import Paginator
import requests
import json
import uuid
from user.models import User, Room, House, Contact, Booking
from Guest.forms import PasswordResetForm, CustomSetPasswordForm
from .utils import content_based_house_recommendation, content_based_room_recommendation
from datetime import datetime
import re
from django.db.models import Q
from django.shortcuts import redirect

def index(request):
    template = loader.get_template('index.html')
    context = {}

    room = Room.objects.all()
    if room.exists():
        # n = len(room)
        # nslide = n // 3 + (n % 3 > 0)
        # rooms = [room, range(1, nslide), n]
        rooms_paginated = Paginator(room, 6)
        rooms_page_number = request.GET.get('rooms_page')
        rooms = rooms_paginated.get_page(rooms_page_number)
        context.update({'room': rooms})

    house = House.objects.all()
    if house.exists():
        # n = len(house)
        # nslide = n // 3 + (n % 3 > 0)
        # houses = [house, range(1, nslide), n]
        houses_paginated = Paginator(house, 6)
        houses_page_number = request.GET.get('houses_page')
        houses = houses_paginated.get_page(houses_page_number)
        context.update({'house': houses})

    return HttpResponse(template.render(context, request))

@login_required(login_url='/login')
def recommended(request):
    user_instance = User.objects.get(email=request.user.email)
    
    recommended_rooms = content_based_room_recommendation(user_instance)
    recommended_houses = content_based_house_recommendation(user_instance)
    
    context = {
        'recommended_rooms': recommended_rooms,
        'recommended_houses': recommended_houses
    }
    
    return render(request, 'recommendation.html', context)

def home(request):
    template = loader.get_template('home.html')
    context = {'result': '', 'msg': 'Search your query'}
    return HttpResponse(template.render(context, request))

# def search(request):
#     template = loader.get_template('home.html')
#     context = {}

#     if request.method == 'GET':
#         typ = request.GET.get('type', '')
#         q = request.GET.get('q', '')
#         context.update({'type': typ, 'q': q})
#         results = {}

#         if typ == 'House' and (bool(House.objects.filter(location=q)) or bool(House.objects.filter(city=q))):
#             results = House.objects.filter(location=q) | House.objects.filter(city=q)
#         elif typ == 'Apartment' and (bool(Room.objects.filter(location=q)) or bool(House.objects.filter(city=q))):
#             results = Room.objects.filter(location=q) | Room.objects.filter(city=q)

#         if not bool(results):
#             messages.success(request, "No matching results for your query..")

#         result = [results, len(results)]
#         context.update({'result': result})

#     return HttpResponse(template.render(context, request))


def search(request):
    template = loader.get_template('home.html')
    context = {}

    if request.method == 'GET':
        typ = request.GET.get('type', '')
        q = request.GET.get('q', '')
        context.update({'type': typ, 'q': q})
        results = {}

        if q == '' or typ == '':
            messages.error(request, "Please enter a valid search query.")
            return redirect('/home/')

        if typ == 'House':
            # Using Q objects and icontains for case-insensitive search
            results = House.objects.filter(Q(district__icontains=q) | Q(city__icontains=q))
        elif typ == 'Apartment':
            # Using Q objects and icontains for case-insensitive search
            results = Room.objects.filter(Q(district__icontains=q) | Q(city__icontains=q))

        if not bool(results):
            messages.success(request, "No matching results for your query..")

        result = [results, len(results)]
        context.update({'result': result})

    return HttpResponse(template.render(context, request))


def about(request):
    template = loader.get_template('about.html')
    context = {'room': Room.objects.all(), 'house': House.objects.all()}
    return HttpResponse(template.render(context, request))

def contact(request):
    template = loader.get_template('contact.html')
    context = {}

    if request.method == 'POST':
        subject = request.POST.get('subject', '')
        email = request.POST.get('email', '')
        body = request.POST.get('body', '')
        
        regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        if not re.search(regex, email):
            template = loader.get_template('register.html')
            context.update({'msg': 'invalid email'})
            return HttpResponse(template.render(context, request))
        
        contact = Contact(subject=subject, email=email, body=body)
        contact.save()
        context.update({'msg': 'Message send to admin'})

    return HttpResponse(template.render(context, request))

def descr(request):
    template = loader.get_template('desc.html')
    context = {}

    if request.method == 'GET':
        id = request.GET.get('id', '')
        try:
            room = Room.objects.get(room_id=id)
            context.update({'val': room, 'type': 'Apartment'})
            user = User.objects.get(email=room.user_email)
        except:
            house = House.objects.get(house_id=id)
            context.update({'val': house, 'type': 'House'})
            user = User.objects.get(email=house.user_email)
        
        context.update({'user': user})

    return HttpResponse(template.render(context, request))


def activate(request, uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.active = True
        user.save()
        messages.success(request, 'Your account has been verified successfully!')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid.')
        return redirect('home')




def activateEmail(request, user, to_email):
    mail_subject = 'Activate your user account'
    message = render_to_string("account_activate_template.html", 
                               {
                                   'user': user.email,
                                   'domain': get_current_site(request).domain,
                                   'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                                   'token': account_activation_token.make_token(user),
                                   'protocol': 'https' if request.is_secure() else 'http',
                               }
                           )
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.content_subtype = "html"
    email.send()
    print("Email sent successfully")
    if email.send():
        messages.success(request, f'{user.name} Your account created successfully! Check your email for verification process.')
    else:
        messages.error(request, f'Problem sending email to {email}, please try again later.')
        
        
def register(request):
    if request.method == 'GET':
        return render(request, 'register.html', {'msg': ''})

    name = request.POST.get('name', '')
    email = request.POST.get('email', '')
    district = request.POST.get('district', '')
    city = request.POST.get('city', '')
    state = request.POST.get('state', '')
    phone = request.POST.get('phone', '')
    pas = request.POST.get('pass', '')
    cpas = request.POST.get('cpass', '')
    
    name_regex = '^[a-zA-Z\s]{2,}$'
    if not re.search(name_regex, name):
        template = loader.get_template('register.html')
        context = {'msg': 'invalid name'}
        return HttpResponse(template.render(context, request))


    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if not re.search(regex, email):
        template = loader.get_template('register.html')
        context = {'msg': 'invalid email'}
        return HttpResponse(template.render(context, request))

    if len(str(phone)) != 10:
        template = loader.get_template('register.html')
        context = {'msg': 'invalid phone number'}
        return HttpResponse(template.render(context, request))

    if pas != cpas:
        template = loader.get_template('register.html')
        context = {'msg': 'password did not match'}
        return HttpResponse(template.render(context, request))

    # already = User.objects.filter(email=email)
    # if bool(already):
    #     template = loader.get_template('register.html')
    #     context = {'msg': 'email already registered'}
        return HttpResponse(template.render(context, request))

    user = User.objects.create_user(
        name=name,
        email=email,
        district=district,
        city=city,
        state=state,
        number=phone,
        password=pas,
    )
    user.active = False
    user.save()
    activateEmail(request, user, user.email)
    messages.success(request, 'Account created successfully, check your email for verification process!!')
    # login(request, user)
    return redirect("login")

def password_reset_request(request):
    form = PasswordResetForm()
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data['email']
            associated_user = User.objects.filter(Q(email=user_email)).first()
            if associated_user:
                mail_subject = 'Password reset request'
                message = render_to_string("password_reset_template.html", 
                               {
                                   'user': associated_user,
                                   'domain': get_current_site(request).domain,
                                   'uid': urlsafe_base64_encode(force_bytes(associated_user.pk)),
                                   'token': account_activation_token.make_token(associated_user),
                                   'protocol': 'https' if request.is_secure() else 'http',
                                   }
                               )
                email = EmailMessage(mail_subject, message, to=[associated_user.email])
                email.send()
                print("Email sent successfully")
                if email.send():
                    messages.success(request, f'{associated_user} Password reset link has been sent to your email!!')
                    return redirect('passwordresetrequest')
                else:
                    messages.error(request, 'Problem while sending email!')

            else:
                return redirect('home')
    return render(request, 'password_reset.html', {'form':form})

def passwordResetConfirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        print(user.email)
    except:
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        if request.method == 'POST':
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Password changed successfully!')
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
        else:
            form = CustomSetPasswordForm(user)
        return render(request, 'password_reset_confirm.html', {'form':form})
    else:
        messages.error(request, 'Activation link is invalid!')
    messages.error(request, 'Something went wrong, redirecting back to homepage')
    return redirect('home')


@login_required    
def password_change(request):
    user = request.user
    if request.method == 'POST':
        form = CustomSetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password changed successfully!')
            return redirect('login')
        else:
            for error in list(form.errors.values()):
                messages.error(request, error)
    form = CustomSetPasswordForm(user)
    return render(request, 'password_change_form.html', {'form':form})


@login_required(login_url='/login')
def profile(request):
    report = Contact.objects.filter(email=request.user.email)
    room = Room.objects.filter(user_email=request.user)
    house = House.objects.filter(user_email=request.user)
    roomcnt = room.count()
    housecnt = house.count()
    reportcnt = report.count()
    bookings = Booking.objects.filter(customer=request.user)
    booking_count = bookings.count()
    # rooms = []
    # houses = []

    # if bool(room):
    #     n = len(room)
    #     nslide = n // 3 + (n % 3 > 0)
    #     rooms = [room, range(1, nslide), n]
    
    # if bool(house):
    #     n = len(house)
    #     nslide = n // 3 + (n % 3 > 0)
    #     houses = [house, range(1, nslide), n]
        
    context = {
        'user': request.user,
        'report': report,
        'reportno': reportcnt,
        'roomno': roomcnt,
        'houseno': housecnt,
        'room': room,
        'house': house,
        'bookings': bookings,
        'booking_count': booking_count,
    }
    
    return render(request, 'profile.html', context=context)

@login_required(login_url='/login')
def post(request):
    print("Post method called")
    if request.method == "GET":
        context = {'user': request.user}
        return render(request, 'post.html', context)
    elif request.method == "POST":
        # try:
        print("Post method on apartment")
        dimention = request.POST.get('dimention', '')
        location = request.POST.get('location', '').lower()
        city = request.POST.get('city', '').lower()
        state = request.POST.get('state', '').lower()
        cost = request.POST.get('cost', '')
        # hall = request.POST.get('hall', '').lower()
        # kitchen = request.POST.get('kitchen', '').lower()
        # balcany = request.POST.get('balcany', '').lower()
        bedroom = request.POST.get('bedroom', '')
        # ac = request.POST.get('AC', '').lower()
        hall = request.POST.get('hall', 'No') == 'Yes'
        kitchen = request.POST.get('kitchen', 'No') == 'Yes'
        balcany = request.POST.get('balcany', 'No') == 'Yes'
        ac = request.POST.get('AC', 'No') == 'Yes'
        desc = request.POST.get('desc', '').upper()
        img = request.FILES.get('img', None)
        print("Checkpoint 1")
        dimention_regex = '^(1[0-5]|[5-9])\s(1[0-5]|[5-9])$'
        # if not re.search(dimention_regex, dimention):
        #     template = loader.get_template('post.html')
        #     context = {'msg': 'invalid dimension Please enter in format like 10 10'}
        #     return HttpResponse(template.render(context, request))

        user_obj = User.objects.filter(email=request.user.email)[0]
        bedroom = int(bedroom)
        cost = int(cost)

        room = Room.objects.create(
            user_email=user_obj,
            dimention=dimention,
            # location=location,
            city=city,
            state=state,
            cost=cost,
            hall=hall,
            kitchen=kitchen,
            balcany=balcany,
            bedrooms=bedroom,
            ac=ac,
            desc=desc,
            img=img,
        )
        print("Room created successfully", room)

        messages.success(request, 'Submitted successfully..')
        return render(request, 'post.html')
        # except Exception as e:
        #     print("An error occurred while creating the room:", e)
        #     return HttpResponse(status=500)

@login_required(login_url='/login')
def posth(request):
    if request.method == "GET":
        context = {'user': request.user}
        return render(request, 'posth.html', context)
    elif request.method == "POST":
        try:
            area = request.POST.get('area', '')
            floor = request.POST.get('floor', '')
            location = request.POST.get('location', '').lower()
            city = request.POST.get('city', '').lower()
            state = request.POST.get('state', '').lower()
            cost = request.POST.get('cost', '')
            # hall = request.POST.get('hall', '').lower()
            # kitchen = request.POST.get('kitchen', '').lower()
            # balcany = request.POST.get('balcany', '').lower()
            bedroom = request.POST.get('bedroom', '')
            # ac = request.POST.get('AC', '').lower()
            hall = request.POST.get('hall', 'No') == 'Yes'
            kitchen = request.POST.get('kitchen', 'No') == 'Yes'
            balcany = request.POST.get('balcany', 'No') == 'Yes'
            ac = request.POST.get('AC', 'No') == 'Yes'
            desc = request.POST.get('desc', '').upper()
            img = request.FILES.get('img', None)

            bedroom = int(bedroom)
            cost = int(cost)

            user_obj = User.objects.filter(email=request.user.email)[0]
            house = House.objects.create(
                user_email=user_obj,
                city=city,
                state=state,
                cost=cost,
                hall=hall,
                kitchen=kitchen,
                balcany=balcany,
                bedrooms=bedroom,
                area=area,
                floor=floor,
                ac=ac,
                desc=desc,
                img=img,
            )

            messages.success(request, 'Submitted successfully..')
            return render(request, 'posth.html')
        except Exception as e:
            print(e)
            return HttpResponse(status=500)

def deleter(request):
    if request.method == 'GET':
        id = request.GET.get('id', '')
        instance = Room.objects.get(room_id=id)
        instance.delete()
        messages.success(request, 'Apartment details deleted successfully..')
    
    return redirect('/profile')

def deleteh(request):
    if request.method == 'GET':
        id = request.GET.get('id', '')
        instance = House.objects.get(house_id=id)
        instance.delete()
        messages.success(request, 'House details deleted successfully..')

    return redirect('/profile')

def login_view(request):
    if request.method == 'GET':
        return render(request, 'login.html')

    email = request.POST.get('email', '')
    password = request.POST.get('password', '')
    user = authenticate(request, email=email, password=password)

    if user is not None:
        login(request, user)
        return redirect("/")
    else:
        template = loader.get_template('login.html')
        context = {'msg': 'Email and password you entered did not match.'}
        return HttpResponse(template.render(context, request))



def user_logout(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect('home')
    else:
        messages.warning(request, 'You must be logged in first!')
        return redirect('/logout/')
 
 
 
# def book_house(request):
#     if request.method == "POST":
#         house_id = request.POST.get('house_id')
#         try:
#             house = House.objects.get(pk=house_id)
#             booking = Booking.objects.create(
#                 house=house,
#                 customer=request.user,
#                 date=datetime.now()
#             )
#             messages.success(request, f'You have successfully booked {house.house_id}.')
#         except House.DoesNotExist:
#             messages.error(request, 'House not found.')
        
#         return redirect('home')  # Redirect to home or appropriate view
#     else:
#         return HttpResponse(status=405)




def book_house(request):
    if request.method == "POST":
        context = {'user': request.user}
        house_id = request.POST.get('house_id')
        context.update({'house_id': house_id})
        try:
            house = House.objects.get(pk=house_id)
            if house.user_email == request.user:
                messages.error(request, 'You cannot book your own house.')
                return redirect('profile')
            if not house.booked:
                uid = uuid.uuid4()
                context['uid'] = uid
                
            #     house.booked = True
            #     house.save()
            #     booking = Booking.objects.create(
            #     house=house,
            #     customer=request.user,
            #     booked=True,
            #     date=datetime.now()
            # )
            #     messages.success(request, f'You have successfully booked {house.house_id}.')
                # pass
            else:
                messages.error(request, f'Sorry, {house.house_id} is already booked.')
        except House.DoesNotExist:
            messages.error(request, 'House not found.')
        
        return render(request, 'pay_with_khalti.html', context)  # Redirect to profile 
    else:
        return HttpResponse(status=405)
    
    
def book_room(request):
    if request.method == "POST":
        context = {'user': request.user}
        room_id = request.POST.get('room_id')
        context.update({'room_id': room_id})
        
        try:
            room = Room.objects.get(pk=room_id)
            if not room.booked:
                uid = uuid.uuid4()
                context['uid'] = uid
                return render(request, 'pay_with_khalti.html', context)
            else:
                messages.error(request, f'Sorry, Room with ID {room.room_id} is already booked.')
            
        except Room.DoesNotExist:
            messages.error(request, 'Room not found.')
        
        return redirect('profile')
        
          # Redirect to profile   
    else:
        return HttpResponse(status=405)



def initkhalti(request):
    url = "https://a.khalti.com/api/v2/epayment/initiate/"
    return_url = request.POST.get('return_url')
    purchase_order_id = request.POST.get('purchase_order_id')
    amount = request.POST.get('amount')
    try:
        house_id = request.POST.get('house_id')
        print('house_id', house_id)
    except:
        house_id = None
    try:
        room_id = request.POST.get('room_id')
    except:
        room_id = None
        
    print('amount', amount)
    print('return_url', return_url)
    print('purchase_order_id', purchase_order_id)
    user = request.user
    
    
    payload_dict = {
        "return_url": return_url,
        "website_url": "http://localhost:8000",
        "amount": amount,
        "purchase_order_id": purchase_order_id,
        # "purchase_order_name": 'Test',
        "customer_info": {
        "name": user.name,
        "email": user.email,
        "phone": user.number
        }
    }
    if house_id is not None:
            payload_dict["purchase_order_name"] = house_id
    elif room_id is not None:
        payload_dict["purchase_order_name"] = room_id
        
    payload = json.dumps(payload_dict)
    headers = {
        'Authorization': 'key a3a997147769444d8622ef339bd356f2',
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
    new_response = json.loads(response.text)
    print(new_response)
    return redirect(new_response['payment_url'])

def verifykhalti(request):
    url = "https://a.khalti.com/api/v2/epayment/lookup/"
    if request.method == "GET":
        headers = {
            'Authorization': 'key a3a997147769444d8622ef339bd356f2',
            'Content-Type': 'application/json',
        }
        pidx = request.GET.get('pidx')
        purchase_order_name = request.GET.get('purchase_order_name')
        data = json.dumps({
            "pidx": pidx
        })
    
        response = requests.request("POST", url, headers=headers, data=data)

        print(response.text)
        new_response = json.loads(response.text)
        
        try:
            house = House.objects.get(house_id=purchase_order_name)
        except:
            house = None
        try:
            room = Room.objects.get(room_id=purchase_order_name)
        except:
            room = None
        
            house.booked = True
            house.save()
            booking = Booking.objects.create(
                house=house,
                customer=request.user,
                booked=True,
                date=datetime.now()
            )
            print(new_response)
            return redirect('profile')
        
        
        if new_response['status'] == 'Completed':
            if house is not None:
                house.booked = True
                house.save()
                booking = Booking.objects.create(
                    house=house,
                    customer=request.user,
                    booked=True,
                    date=datetime.now()
                )
                return redirect('profile')
            elif room is not None:
                room.booked = True
                room.save()
                booking = Booking.objects.create(
                    room=room,
                    customer=request.user,
                    booked=True,
                    date=datetime.now()
                )
                return redirect('profile')
            
            print(new_response)
            return redirect('profile')
        



























































   
# chat view
from django.shortcuts import render

def chat_view(request):
    return render(request, 'chat.html')
