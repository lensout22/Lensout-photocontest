import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import PageNotAnInteger, Paginator, EmptyPage
from django.db.models import Sum, Count, Q, F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout, authenticate, login, update_session_auth_hash
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_text, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.core.paginator import Paginator
from users.models import Contract, Subscriber
from users.forms import *
from users.tokens import account_activation_token
from django.contrib.sites.shortcuts import get_current_site


def Signup(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == "POST":
            isvalid = 0
            usernameField = request.POST.get('usernameForm')
            emailField = request.POST.get('emailForm')
            firstnameField = request.POST.get('firstnameForm')
            lastnameField = request.POST.get('lastnameForm')
            password1Field = request.POST.get('password1Form')
            password2Field = request.POST.get('password2Form')

            msg_tag = "register_success"
            msg = ""
            if User.objects.filter(username=usernameField).exists():
                msg = "Username have already used.Try with another"
                isvalid = isvalid + 1
                msg_tag = "register_error"
            elif password1Field != password2Field:
                msg = "password not matching!"
                isvalid = isvalid + 1
                msg_tag = "register_error"
            if isvalid == 0:
                user = User.objects.create_user(
                    username=usernameField, email=emailField, first_name=firstnameField, last_name=lastnameField,
                    password=password1Field,
                )
                user.is_active = False
                user.save()
                user.refresh_from_db()

                msg = "Your account is create successfully.please confirm your email to continue"
                current_site = get_current_site(request)
                mail_subject = 'Activate your  account.'
                message = render_to_string('Auth/acc_activate_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                })
                to_email = user.email
                email = EmailMessage(
                    mail_subject, message, to=[to_email]
                )
                email.send()

            messages.success(request, msg, extra_tags=msg_tag)
            return redirect('signup')
        else:
            return render(request, 'users/register.html')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('update_profile')
    else:
        return HttpResponse('Activation link is invalid!')


@login_required(login_url='login')
def UpdateProfile(request):
    # try:
    if request.method == "POST":
        gender = request.POST.get('gender')
        role = request.POST.get('role')
        city = request.POST.get('cityField')
        phone = request.POST.get('phoneForm')
        about = request.POST.get('about')
        photo = request.FILES['photoFile']
        print(photo)
        user = Profile.objects.get(user=request.user)
        user.city = city
        user.role = role
        user.gender = gender
        user.phone = phone
        user.about = about
        if photo == "":
            photo = user.photo.url
        user.photo = photo
        user.save()
        messages.success(request, "Profile Update Successfully", extra_tags="profile_update")
        return redirect('update_profile')
    else:
        user = []
        if Profile.objects.filter(user=request.user).exists():
            user = Profile.objects.get(user=request.user)
        context = {
            "user": user
        }
        return render(request, 'users/complete_profile.html', context)
    # except:
    #     return HttpResponse("<h1>Page Not Found</h1>")


def Login(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            username = request.POST.get('usernameForm')
            password = request.POST.get('password1Form')
            valuenext = request.POST.get('next')
            msg_tag = "login_error"
            msg = ""
            if User.objects.filter(username=username).exists():
                if not get_object_or_404(User, username=username).is_active:
                    msg = "Account is not active"
                else:
                    user = authenticate(request, username=username, password=password)
                    if user is not None:
                        login(request, user)
                        if valuenext != "":
                            return redirect(valuenext)
                        return redirect('home')
                    else:
                        msg = "Enter correct email & password"
            else:
                msg = "Username is not register yet"
            messages.info(request, msg, extra_tags=msg_tag)
            return redirect('login')
        else:
            return render(request, 'login.html')

@login_required(login_url='login')
def Logout(request):
    logout(request)
    return redirect('login')


def ContactUs(request):
    if request.method == "POST":
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        subject = request.POST['subject']
        message = request.POST['comment']
        Contract.objects.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message,
        ).save()
        messages.success(request, "Your Message is Delivered to Admin .Please wait for dashboard Reply",extra_tags="add_contact")
        return redirect('contact')
    else:
        return render(request, 'contact.html')


def ContestHome(request):
    cons = Contest.objects.all().filter(winner=None).order_by('-id')
    con = Contest.objects.all()
    photoco = ContestMaterial.objects.all()

    l = 0
    for p in photoco:
        l = l + p.total_loved()
    w = 0
    for c in con:
        if c.total_winner() == 1:
            w = w + 1
    paginator = Paginator(cons, 4)
    page = request.GET.get('page')
    cons = paginator.get_page(page)
    context = {
        'contest': cons,
        'conn': photoco,
        'loved': l,
        'winner': w,
        'co': con,
    }
    return render(request, 'photocontest-list1.html', context)


@login_required(login_url='login')
def ViewContest(request, id):
    contest = get_object_or_404(Contest, id=id)
    is_joined = False
    is_upload = False
    if contest.joined.filter(id=request.user.id).exists():
        is_joined = True

    for f in Contest.objects.filter(id=id):
        t = f.contest_attends.all()
    paginator = Paginator(t, 9)
    page = request.GET.get('page')
    t = paginator.get_page(page)
    is_view = False
    if contest.contest_attends.filter(author=request.user).exists():
        is_view = True
    if contest.contest_attends.filter(author=request.user).exists():
        is_upload = True
    is_win = False
    winner = contest.winner.all()
    win = ''
    for i in winner:
        win = i
    if winner:
        is_win = True

    context = {
        'contest': contest,
        'is_joined': is_joined,
        'contester': t,
        'is_view': is_view,
        'is_upload': is_upload,
        'winner': win,
        'is_win': is_win,
    }
    return render(request, 'single-contest1.html', context)


@login_required(login_url='login')
def JoinContest(request):
    contest_id = request.POST['joinc']
    contest = get_object_or_404(Contest, id=contest_id)
    if contest.type == "free":
        if contest.joined.filter(id=request.user.id).exists():
            return HttpResponse("<h1>You have already joined this Contest</h1>")
        else:
            contest.joined.add(request.user)
            contest.save()
            return redirect(contest.get_absolute_url())
    elif contest.type == "paid":
        if Subscriber.objects.filter(subscriber=request.user).exists():
            if contest.joined.filter(id=request.user.id).exists():
                return HttpResponse("<h1>You have already joined this Contest</h1>")
            else:
                contest.joined.add(request.user)
                contest.save()
                return redirect(contest.get_absolute_url())
        else:
            return render(request, 'users/subscribe.html')


@login_required(login_url='login')
def Checkout(request, pack):
    package = ""
    price = 0.0
    if pack == "1M":
        package = "30  Days"
        price = price + 10.0

    elif pack == "3M":
        package = "3 Month"
        price = price + 25.0

    elif pack == "12M":
        package = "1 Year"
        price = price + 60.0
    user = request.user
    context = {
        'pack': package,
        'price': price,
        'username': user,
    }
    return render(request, 'users/checkout.html', context)


@login_required(login_url='login')
def SubscriptionCompleted(request):
    body = json.loads(request.body)
    user = (body['subscription_user'])
    pack = (body['packname'])
    current_date = date.today()
    subs = ''
    price = 0
    if pack == "30  Days":
        days = timedelta(days=30)
        subs = current_date + days
        price = 20
    elif pack == "3 Month":
        days = timedelta(days=90)
        subs = current_date + days
        price = 50
    elif pack == "1 Year":
        days = timedelta(days=366)
        subs = current_date + days
        price = 100
    try:
        if Subscriber.objects.filter(subscriber=request.user).exists():
            user = Subscriber.objects.get(subscriber=request.user)

            if user.until_date < current_date:
                user.until_date = subs
                user.payment += price
                user.save()

        else:
            new = Subscriber.objects.create(
                subscriber=request.user,
                until_date=subs,
                payment=price

            )
            new.save()

    except:
        pass
    return JsonResponse('Sunscription completed', safe=False)


@login_required(login_url='login')
def UploadPhoto(request, id):
    contest = get_object_or_404(Contest, id=id)
    context = {
        'contest': contest,
    }
    if request.method == "POST":
        pic = request.FILES['photo']
        contest.contest_attends.create(
            author=request.user,
            photo=pic
        ).save()
        messages.success(request, 'Photo Upload Successfully')
        return redirect(contest.upload_absolute_url())
    else:
        return render(request, 'users/upload_photo.html', context)


@login_required(login_url='login')
def ContestLove(request):
    contest = get_object_or_404(Contest, id=request.POST['pho'])
    cmaterial = request.POST['love']
    con = get_object_or_404(ContestMaterial, id=cmaterial)
    if con.love.filter(id=request.user.id).exists():
        con.love.remove(request.user)
        con.save()
    else:
        con.love.add(request.user)
        con.save()
    return redirect(contest.get_absolute_url())


@login_required(login_url='login')
def RemovePhoto(request):
    contest = get_object_or_404(Contest, id=request.POST['contestname'])
    if contest.post_by == request.user:
        photo = request.POST['removep']
        kk = get_object_or_404(ContestMaterial, id=photo)
        kk.delete()
        return redirect(contest.get_absolute_url())
    else:
        return HttpResponse("You can't")


@login_required(login_url='login')
def Winner(request, contest, photom):
    contest = get_object_or_404(Contest, id=contest)
    kk = get_object_or_404(ContestMaterial, id=photom)
    is_allow = False
    context = {
        'contest': contest,
        'photomaterial': kk,
    }
    if contest.post_by == request.user:
        is_allow = True
    if request.method == "POST" and is_allow == True:
        contest.winner.add(kk.author)
        contest.save()
        Profile.objects.filter(user=kk.author).update(
            balance=F('balance') + contest.winner_ammount)
        return redirect(contest.get_absolute_url())
    else:
        return render(request, 'users/winner_select.html', context)


@login_required(login_url='login')
def Dashboard(request):
    cons = Contest.objects.filter(post_by=request.user)
    total_cons = cons.count()
    running_cons = cons.filter(winner=None).count()
    sum = 0
    for i in cons:
        sum = sum + i.winner_ammount

    wincontest = Contest.objects.filter(winner=request.user)
    s = wincontest.count()
    total_ammount_win = 0
    for i in wincontest:
        total_ammount_win = total_ammount_win + i.winner_ammount
    total_join = 0
    con = Contest.objects.filter(joined=request.user)
    for i in con:
        total_join = total_join + i.joined.count()

    total_photo_upload = 0
    for i in ContestMaterial.objects.filter(author=request.user):
        total_photo_upload = total_photo_upload + 1
    withrequest = RequestWithdraw.objects.filter(request_user=request.user)
    context = {
        'total_contest': total_cons,
        'running_contest': running_cons,
        'close_cons': total_cons - running_cons,
        'total_spend': sum,
        'winner_contest': s,
        'total_win_ammount': total_ammount_win,
        'total_join': total_join,
        'withdraw': withrequest,
        'total_photo_upload': total_photo_upload,
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required(login_url='login')
def PHotoUpdate(request):
    if request.method == "POST":
        photo = request.FILES['photo']
        user = Profile.objects.get(user=request.user)
        user.photo = photo
        user.save()
        messages.success(request, "Photo Update")
        return redirect('profile')


@login_required(login_url='login')
def UserProfile(request):
    if request.method == "POST":
        fname = request.POST['fname']
        lname = request.POST['lname']
        gender = request.POST['gender']
        role = request.POST['role']
        city = request.POST['city']
        phone = request.POST['phone']
        about = request.POST['about']
        uss = User.objects.get(username=request.user)
        uss.first_name = fname
        uss.last_name = lname
        uss.save()
        us = Profile.objects.get(user=request.user)
        us.city = city
        us.phone = phone
        us.role = role
        us.gender = gender
        us.about = about
        us.save()
        messages.success(request, "Profile Updated")
        return redirect('profile')
    else:
        return render(request, 'dashboard/user.html')


@login_required(login_url='login')
def AddCont(request):
    val = Profile.objects.get(user=request.user)
    if request.method == "POST":
        s_Date = request.POST.get('startDate')
        e_Date = request.POST.get('endDate')
        contest_Title = request.POST.get('titleContest')
        contest_Amount = request.POST.get('winningAmount')
        contest_Type = request.POST.get('contestType')
        contest_Details = request.POST.get('details')
        contest_Photo = request.FILES['photoFile']
        start_Date = s_Date.split("T")[0]
        start_Time = s_Date.split("T")[1]
        end_Date = e_Date.split("T")[0]
        end_Time = e_Date.split("T")[1]
        amount = float(contest_Amount)
        if val.balance < amount:
            msg = "Your balance is insuficiant"
        else:
            contest = Contest.objects.create(
                post_by=request.user, title=contest_Title, details=contest_Details, demo_pic=contest_Photo,
                start_on=start_Date, start_time=start_Time, end_on=end_Date, end_time=end_Time, winner_ammount=amount,
                type=contest_Type
            )
            contest.save()
            val.balance = val.balance - amount
            val.save()
            msg = "Photo Contest Saved Succesfully"
        messages.success(request, msg)
        return redirect('addcontest')
    else:
        return render(request, 'users/addcontest.html')


@login_required(login_url='login')
def ManageContest(request):
    contest = Contest.objects.filter(post_by=request.user)

    context = {
        'contest': contest,
    }
    return render(request, 'users/contestlist.html', context)


@login_required(login_url='login')
def DeleteContest(request):
    id = request.POST['delc']
    blog = Contest.objects.get(id=id)
    if blog.post_by == request.user:
        blog.delete()
        return redirect('managecontest')
    else:
        return HttpResponse("<h1>You are not owner of this contest</h1>")


@login_required(login_url='login')
def UpdateContest(request, id):
    post = Contest.objects.get(id=id)
    if post.post_by == request.user:
        if request.method == "POST":
            s_Date = request.POST.get('startDate')
            e_Date = request.POST.get('endDate')
            contest_Title = request.POST.get('titleContest')
            contest_Amount = request.POST.get('winningAmount')
            contest_Type = request.POST.get('contestType')
            contest_Details = request.POST.get('details')
            start_Date = s_Date.split("T")[0]
            start_Time = s_Date.split("T")[1]
            end_Date = e_Date.split("T")[0]
            end_Time = e_Date.split("T")[1]
            amount = float(contest_Amount)
            post.title = contest_Title
            post.type = contest_Type
            post.winner_ammount = amount
            post.details = contest_Details
            if 'photoFile' in request.FILES:
                print(request.FILES['photoFile'])
                post.demo_pic = request.FILES['photoFile']
            post.start_on = start_Date
            post.start_time = start_Time
            post.end_on = end_Date
            post.end_time = end_Time
            post.save()

            messages.success(request, 'Contest Updated Successfully')
            return redirect(post.update_absolute_url())
        else:
            context = {
                'contest': post,
            }
            return render(request, 'users/updatecontest.html', context)

    else:
        return HttpResponse("<h1>Your are not allow to delete the post</h1>")


@login_required(login_url='login')
def AddBalance(request):
    if request.method == "POST":
        val = request.POST['money']
        context = {
            'money': val,
            'usxx': request.user,
        }
        return render(request, 'users/addbalance.html', context)
    else:
        return render(request, 'users/chosebalance.html')


@login_required(login_url='login')
def paymentComplated(request):
    body = json.loads(request.body)
    print('BODY', body)
    balance = body['owner']
    BalanceAdd.objects.create(
        owner=request.user, amount=balance
    ).save()
    Profile.objects.filter(user=request.user).update(
        balance=F('balance') + balance)
    return redirect('addbalance')


@login_required(login_url='login')
def PasswordChange(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(
                request, 'Your password was successfully updated!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {
        'form': form
    })


@login_required(login_url='login')
def RequestPayment(request):
    if request.method == "POST":
        val = request.POST['ammount_']
        pay = request.POST['paypal']
        RequestWithdraw.objects.create(
            request_user=request.user, paypal=pay, payment=float(int(val)-int(val)*0.10)
        ).save()
        Profile.objects.filter(user=request.user).update(
            balance=F('balance') - val)
        messages.success(request, "Your Withdrawal Request accept successfully")
        return redirect('requestpayment')
    else:
        return render(request, 'users/requestwithdraw.html')


def Galary(request):
    img = ContestMaterial.objects.all()
    paginator = Paginator(img, 9)
    page = request.GET.get('page')
    img = paginator.get_page(page)
    context = {
        'img': img,
    }
    return render(request, 'gallery2.html', context)


def AboutmeDetails(request):
    ad = Aboutme.objects.last()
    context = {
        'profile': ad,
    }
    return render(request, 'about-me.html', context)


@login_required(login_url='login')
def FeedbackView(request):
    message = ""
    ratting = 0
    obj=""
    if Feedback.objects.filter(user=request.user).exists():
        obj=Feedback.objects.get(user=request.user)
    print(obj)
    if request.method == "POST":
        message = request.POST.get('feedback')
        ratting = request.POST.get('ratting')
        print(message,ratting)
        if obj!="":
            obj = Feedback.objects.get(user=request.user)
            obj.ratting = ratting
            obj.feedback = message
            obj.status = False
            obj.save()
            msg = "Your Feedback is Updated wait for Admin approval"
        else:
            feedback = Feedback.objects.create(
                user=request.user,
                feedback=message,
                ratting=ratting
            )
            feedback.save()
            msg = "Your Feedback is Saved wait for Admin approval"
        messages.success(request,msg)
        return redirect('feedback')
    else:
        context={
            'obj':obj,
        }
        return render(request, 'dashboard/feedback.html', context)
